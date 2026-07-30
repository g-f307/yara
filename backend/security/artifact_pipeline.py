"""Pipeline seguro para sincronização e inspeção de artefatos científicos."""

from __future__ import annotations

import asyncio
import csv
import hashlib
import ipaddress
import json
import os
import shutil
import socket
import stat
import tempfile
import uuid
import zipfile
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path, PurePosixPath
from urllib.parse import urljoin, urlsplit

import httpx

ALLOWED_EXTENSIONS = {".tsv", ".csv", ".qza", ".qzv", ".biom"}
REDIRECT_CODES = {301, 302, 303, 307, 308}
HTML_PREFIXES = (b"<!doctype html", b"<html", b"<script", b"<?php")
EXECUTABLE_PREFIXES = (b"MZ", b"\x7fELF", b"#!")
ZIP_MAGIC = b"PK\x03\x04"
HDF5_MAGIC = b"\x89HDF\r\n\x1a\n"
GENERIC_MIME_TYPES = {"", "application/octet-stream", "binary/octet-stream"}


class ArtifactSecurityError(ValueError):
    """Erro esperado, seguro para ser convertido em resposta pública."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.public_message = message


class ArtifactStatus(StrEnum):
    QUARANTINED = "QUARANTINED"
    VALIDATING = "VALIDATING"
    VALID = "VALID"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class ArtifactLimits:
    max_download_bytes: int
    max_zip_entries: int
    max_uncompressed_bytes: int
    max_compression_ratio: float
    max_redirects: int
    connect_timeout_seconds: float
    read_timeout_seconds: float

    @classmethod
    def from_env(cls) -> "ArtifactLimits":
        return cls(
            max_download_bytes=int(
                os.getenv("MAX_FILE_SIZE_BYTES", str(128 * 1024 * 1024))
            ),
            max_zip_entries=int(os.getenv("MAX_ZIP_ENTRIES", "2000")),
            max_uncompressed_bytes=int(
                os.getenv("MAX_ZIP_UNCOMPRESSED_BYTES", str(512 * 1024 * 1024))
            ),
            max_compression_ratio=float(os.getenv("MAX_ZIP_COMPRESSION_RATIO", "100")),
            max_redirects=int(os.getenv("MAX_DOWNLOAD_REDIRECTS", "3")),
            connect_timeout_seconds=float(os.getenv("DOWNLOAD_CONNECT_TIMEOUT_SECONDS", "5")),
            read_timeout_seconds=float(os.getenv("DOWNLOAD_READ_TIMEOUT_SECONDS", "30")),
        )


def validate_artifact_configuration() -> None:
    try:
        limits = ArtifactLimits.from_env()
    except ValueError as exc:
        raise RuntimeError(
            "Os limites de artefatos devem usar valores numéricos válidos."
        ) from exc
    numeric_values = (
        limits.max_download_bytes,
        limits.max_zip_entries,
        limits.max_uncompressed_bytes,
        limits.max_compression_ratio,
        limits.connect_timeout_seconds,
        limits.read_timeout_seconds,
    )
    if any(value <= 0 for value in numeric_values) or limits.max_redirects < 0:
        raise RuntimeError("Os limites de artefatos devem ser maiores que zero.")
    if not allowed_storage_hosts():
        raise RuntimeError("ALLOWED_STORAGE_HOSTS deve conter ao menos um domínio.")


@dataclass
class ArtifactRecord:
    id: str
    original_name: str
    physical_name: str
    extension: str
    sha256: str
    size: int
    status: str


def normalize_project_id(project_id: str) -> str:
    try:
        normalized = str(uuid.UUID(project_id))
    except (ValueError, AttributeError) as exc:
        raise ArtifactSecurityError(
            "INVALID_PROJECT_ID",
            "Identificador de projeto inválido.",
        ) from exc
    if normalized != project_id.lower():
        raise ArtifactSecurityError(
            "INVALID_PROJECT_ID",
            "Identificador de projeto inválido.",
        )
    return normalized


def safe_project_dir(storage_path: str | Path, project_id: str) -> Path:
    root = Path(storage_path).resolve()
    target = (root / normalize_project_id(project_id)).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ArtifactSecurityError(
            "UNSAFE_STORAGE_PATH",
            "Caminho de armazenamento inválido.",
        ) from exc
    return target


def allowed_storage_hosts() -> tuple[str, ...]:
    configured = os.getenv(
        "ALLOWED_STORAGE_HOSTS",
        "utfs.io,ufs.sh,*.ufs.sh",
    )
    return tuple(host.strip().lower().rstrip(".") for host in configured.split(",") if host.strip())


def _host_matches(host: str, pattern: str) -> bool:
    return host == pattern or (
        pattern.startswith("*.") and host.endswith(pattern[1:]) and host != pattern[2:]
    )


def _is_forbidden_ip(address: str) -> bool:
    ip = ipaddress.ip_address(address.split("%", 1)[0])
    return not ip.is_global


async def resolve_public_addresses(host: str, port: int) -> set[str]:
    try:
        infos = await asyncio.get_running_loop().run_in_executor(
            None,
            lambda: socket.getaddrinfo(
                host,
                port,
                type=socket.SOCK_STREAM,
            ),
        )
    except socket.gaierror as exc:
        raise ArtifactSecurityError(
            "URL_DNS_FAILED",
            "Não foi possível validar o endereço do arquivo.",
        ) from exc

    addresses = {info[4][0] for info in infos}
    if not addresses or any(_is_forbidden_ip(address) for address in addresses):
        raise ArtifactSecurityError(
            "URL_PRIVATE_ADDRESS",
            "O endereço do arquivo não é permitido.",
        )
    return addresses


async def validate_remote_url(url: str) -> str:
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError as exc:
        raise ArtifactSecurityError("URL_INVALID", "URL do arquivo inválida.") from exc

    environment = os.getenv("ENVIRONMENT", "development").lower()
    permitted_schemes = {"https"} if environment == "production" else {"https", "http"}
    if parsed.scheme.lower() not in permitted_schemes:
        raise ArtifactSecurityError(
            "URL_SCHEME_BLOCKED",
            "O protocolo da URL do arquivo não é permitido.",
        )
    if parsed.username or parsed.password or not parsed.hostname:
        raise ArtifactSecurityError("URL_INVALID", "URL do arquivo inválida.")

    host = parsed.hostname.lower().rstrip(".")
    if not any(_host_matches(host, pattern) for pattern in allowed_storage_hosts()):
        raise ArtifactSecurityError(
            "URL_HOST_BLOCKED",
            "O domínio de armazenamento não é autorizado.",
        )
    if host == "localhost" or host.endswith(".localhost"):
        raise ArtifactSecurityError(
            "URL_PRIVATE_ADDRESS",
            "O endereço do arquivo não é permitido.",
        )

    try:
        parsed_ip = ipaddress.ip_address(host.split("%", 1)[0])
    except ValueError:
        await resolve_public_addresses(host, port or (443 if parsed.scheme == "https" else 80))
    else:
        if not parsed_ip.is_global:
            raise ArtifactSecurityError(
                "URL_PRIVATE_ADDRESS",
                "O endereço do arquivo não é permitido.",
            )
    return url


def validate_original_name(name: str) -> tuple[str, str]:
    if not name or len(name) > 255 or "\x00" in name:
        raise ArtifactSecurityError("INVALID_FILE_NAME", "Nome de arquivo inválido.")
    path = PurePosixPath(name.replace("\\", "/"))
    if path.is_absolute() or len(path.parts) != 1 or any(part in {"", ".", ".."} for part in path.parts):
        raise ArtifactSecurityError("UNSAFE_FILE_NAME", "Nome de arquivo inválido.")
    extension = Path(name).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise ArtifactSecurityError(
            "EXTENSION_NOT_ALLOWED",
            "A extensão do arquivo não é permitida.",
        )
    return name, extension


def _reject_disguised_content(prefix: bytes) -> None:
    stripped = prefix.lstrip().lower()
    if any(stripped.startswith(value) for value in HTML_PREFIXES):
        raise ArtifactSecurityError(
            "CONTENT_TYPE_MISMATCH",
            "O conteúdo do arquivo não corresponde à extensão informada.",
        )
    if any(prefix.startswith(value) for value in EXECUTABLE_PREFIXES):
        raise ArtifactSecurityError(
            "CONTENT_TYPE_MISMATCH",
            "O conteúdo do arquivo não corresponde à extensão informada.",
        )


def _validate_table(path: Path, extension: str) -> None:
    prefix = path.read_bytes()[:4096]
    _reject_disguised_content(prefix)
    if b"\x00" in prefix:
        raise ArtifactSecurityError(
            "CONTENT_TYPE_MISMATCH",
            "O conteúdo do arquivo não corresponde à extensão informada.",
        )
    try:
        text = prefix.decode("utf-8-sig")
        delimiter = "," if extension == ".csv" else "\t"
        rows = list(csv.reader(text.splitlines(), delimiter=delimiter))
    except (UnicodeDecodeError, csv.Error) as exc:
        raise ArtifactSecurityError(
            "INVALID_TABLE",
            "A tabela enviada não possui uma estrutura válida.",
        ) from exc
    meaningful = [row for row in rows if row and not row[0].startswith("#")]
    if len(meaningful) < 2 or len(meaningful[0]) < 2:
        raise ArtifactSecurityError(
            "INVALID_TABLE",
            "A tabela enviada não possui uma estrutura válida.",
        )


def _is_symlink(member: zipfile.ZipInfo) -> bool:
    return stat.S_ISLNK(member.external_attr >> 16)


def inspect_qiime_zip(path: Path, limits: ArtifactLimits | None = None) -> None:
    limits = limits or ArtifactLimits.from_env()
    try:
        archive = zipfile.ZipFile(path)
    except (zipfile.BadZipFile, OSError) as exc:
        raise ArtifactSecurityError(
            "INVALID_QIIME_ARCHIVE",
            "O artefato QIIME 2 não é um arquivo ZIP válido.",
        ) from exc

    with archive:
        members = archive.infolist()
        if not members or len(members) > limits.max_zip_entries:
            raise ArtifactSecurityError(
                "ZIP_ENTRY_LIMIT",
                "O artefato QIIME 2 excede os limites de segurança.",
            )

        total_uncompressed = 0
        seen: set[str] = set()
        names: set[str] = set()
        for member in members:
            normalized_name = member.filename.replace("\\", "/")
            member_path = PurePosixPath(normalized_name)
            if (
                member_path.is_absolute()
                or ".." in member_path.parts
                or normalized_name.startswith("/")
                or _is_symlink(member)
            ):
                raise ArtifactSecurityError(
                    "UNSAFE_ZIP_ENTRY",
                    "O artefato QIIME 2 contém uma entrada insegura.",
                )
            folded = normalized_name.casefold()
            if folded in seen:
                raise ArtifactSecurityError(
                    "DUPLICATE_ZIP_ENTRY",
                    "O artefato QIIME 2 contém entradas duplicadas.",
                )
            seen.add(folded)
            names.add(normalized_name.rstrip("/"))
            total_uncompressed += member.file_size
            ratio = member.file_size / max(member.compress_size, 1)
            if (
                total_uncompressed > limits.max_uncompressed_bytes
                or ratio > limits.max_compression_ratio
            ):
                raise ArtifactSecurityError(
                    "ZIP_EXPANSION_LIMIT",
                    "O artefato QIIME 2 excede os limites de descompactação.",
                )

        roots = {PurePosixPath(name).parts[0] for name in names if PurePosixPath(name).parts}
        if len(roots) != 1:
            raise ArtifactSecurityError(
                "INVALID_QIIME_STRUCTURE",
                "O artefato não possui a estrutura mínima esperada do QIIME 2.",
            )
        root = next(iter(roots))
        if f"{root}/VERSION" not in names or f"{root}/metadata.yaml" not in names:
            raise ArtifactSecurityError(
                "INVALID_QIIME_STRUCTURE",
                "O artefato não possui a estrutura mínima esperada do QIIME 2.",
            )


def validate_artifact_content(path: Path, extension: str, limits: ArtifactLimits) -> None:
    size = path.stat().st_size
    if size == 0:
        raise ArtifactSecurityError("EMPTY_FILE", "O arquivo enviado está vazio.")
    prefix = path.read_bytes()[:16]
    if extension in {".qza", ".qzv"}:
        if not prefix.startswith(ZIP_MAGIC):
            raise ArtifactSecurityError(
                "CONTENT_TYPE_MISMATCH",
                "O conteúdo do arquivo não corresponde à extensão informada.",
            )
        inspect_qiime_zip(path, limits)
    elif extension in {".tsv", ".csv"}:
        _validate_table(path, extension)
    elif extension == ".biom":
        _reject_disguised_content(prefix)
        if not prefix.startswith(HDF5_MAGIC):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ArtifactSecurityError(
                    "INVALID_BIOM",
                    "O arquivo BIOM não possui uma estrutura válida.",
                ) from exc
            if not isinstance(data, dict) or "format" not in data:
                raise ArtifactSecurityError(
                    "INVALID_BIOM",
                    "O arquivo BIOM não possui uma estrutura válida.",
                )


def validate_declared_mime(content_type: str, extension: str) -> None:
    mime = content_type.split(";", 1)[0].strip().lower()
    if mime in GENERIC_MIME_TYPES:
        return
    allowed = {
        ".tsv": {"text/tab-separated-values", "text/plain"},
        ".csv": {"text/csv", "text/plain"},
        ".qza": {"application/zip", "application/x-zip-compressed"},
        ".qzv": {"application/zip", "application/x-zip-compressed"},
        ".biom": {"application/json", "application/x-hdf5"},
    }
    if mime not in allowed[extension]:
        raise ArtifactSecurityError(
            "MIME_TYPE_MISMATCH",
            "O tipo declarado do arquivo não corresponde à extensão informada.",
        )


async def _stream_response_to_file(
    response: httpx.Response,
    destination: Path,
    max_bytes: int,
) -> tuple[int, str]:
    received = 0
    digest = hashlib.sha256()
    with destination.open("wb") as output:
        async for chunk in response.aiter_bytes(64 * 1024):
            received += len(chunk)
            if received > max_bytes:
                raise ArtifactSecurityError(
                    "DOWNLOAD_SIZE_LIMIT",
                    "O arquivo excede o limite máximo permitido.",
                )
            digest.update(chunk)
            output.write(chunk)
    return received, digest.hexdigest()


async def download_to_quarantine(
    client: httpx.AsyncClient,
    url: str,
    destination: Path,
    limits: ArtifactLimits,
    extension: str | None = None,
) -> tuple[int, str]:
    current_url = url
    for redirect_count in range(limits.max_redirects + 1):
        await validate_remote_url(current_url)
        async with client.stream("GET", current_url) as response:
            if response.status_code in REDIRECT_CODES:
                location = response.headers.get("location")
                if not location or redirect_count >= limits.max_redirects:
                    raise ArtifactSecurityError(
                        "REDIRECT_LIMIT",
                        "O endereço do arquivo excedeu o limite de redirecionamentos.",
                    )
                current_url = urljoin(current_url, location)
                continue
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise ArtifactSecurityError(
                    "DOWNLOAD_HTTP_ERROR",
                    "Não foi possível baixar o arquivo informado.",
                ) from exc
            if extension:
                validate_declared_mime(
                    response.headers.get("content-type", ""),
                    extension,
                )
            content_length = response.headers.get("content-length")
            if content_length:
                try:
                    declared_length = int(content_length)
                except ValueError:
                    declared_length = 0
                if declared_length > limits.max_download_bytes:
                    raise ArtifactSecurityError(
                        "DOWNLOAD_SIZE_LIMIT",
                        "O arquivo excede o limite máximo permitido.",
                    )
            return await _stream_response_to_file(
                response,
                destination,
                limits.max_download_bytes,
            )
    raise ArtifactSecurityError(
        "REDIRECT_LIMIT",
        "O endereço do arquivo excedeu o limite de redirecionamentos.",
    )


class ArtifactStore:
    def __init__(self, storage_path: str | Path) -> None:
        self.storage_path = Path(storage_path)
        self.limits = ArtifactLimits.from_env()

    def _manifest_path(self, project_dir: Path) -> Path:
        return project_dir / ".artifacts.json"

    def _load_manifest(self, project_dir: Path) -> list[dict]:
        path = self._manifest_path(project_dir)
        if not path.exists():
            return []
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            return value if isinstance(value, list) else []
        except (OSError, json.JSONDecodeError):
            return []

    def _save_manifest(self, project_dir: Path, records: list[dict]) -> None:
        manifest = self._manifest_path(project_dir)
        temporary = manifest.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(records, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        os.replace(temporary, manifest)

    def valid_records(self, project_id: str) -> list[ArtifactRecord]:
        project_dir = safe_project_dir(self.storage_path, project_id)
        return [
            ArtifactRecord(**record)
            for record in self._load_manifest(project_dir)
            if record.get("status") == ArtifactStatus.VALID
            and set(record)
            == {
                "id",
                "original_name",
                "physical_name",
                "extension",
                "sha256",
                "size",
                "status",
            }
        ]

    def import_local_validated(
        self,
        project_id: str,
        source: str | Path,
        original_name: str,
    ) -> ArtifactRecord:
        """Importa fixture local após aplicar as mesmas validações de conteúdo."""
        project_dir = safe_project_dir(self.storage_path, project_id)
        project_dir.mkdir(parents=True, exist_ok=True)
        original_name, extension = validate_original_name(original_name)
        source = Path(source)
        validate_artifact_content(source, extension, self.limits)
        digest = hashlib.sha256()
        with source.open("rb") as input_file:
            while chunk := input_file.read(64 * 1024):
                digest.update(chunk)
        sha256 = digest.hexdigest()
        records = self._load_manifest(project_dir)
        duplicate = next(
            (
                record
                for record in records
                if record.get("sha256") == sha256
                and record.get("status") == ArtifactStatus.VALID
            ),
            None,
        )
        if duplicate:
            return ArtifactRecord(**duplicate)

        artifact_id = str(uuid.uuid4())
        physical_name = f"{artifact_id}{extension}"
        destination = project_dir / physical_name
        with source.open("rb") as input_file, destination.open("xb") as output_file:
            shutil.copyfileobj(input_file, output_file, length=64 * 1024)
        record = ArtifactRecord(
            id=artifact_id,
            original_name=original_name,
            physical_name=physical_name,
            extension=extension,
            sha256=sha256,
            size=source.stat().st_size,
            status=ArtifactStatus.VALID,
        )
        records.append(asdict(record))
        try:
            self._save_manifest(project_dir, records)
        except OSError:
            destination.unlink(missing_ok=True)
            raise
        return record

    async def sync_one(
        self,
        client: httpx.AsyncClient,
        project_id: str,
        source_url: str,
        original_name: str,
    ) -> ArtifactRecord:
        project_dir = safe_project_dir(self.storage_path, project_id)
        project_dir.mkdir(parents=True, exist_ok=True)
        quarantine_dir = project_dir / ".quarantine"
        quarantine_dir.mkdir(mode=0o700, exist_ok=True)
        original_name, extension = validate_original_name(original_name)
        artifact_id = str(uuid.uuid4())
        temporary_path: Path | None = None

        try:
            descriptor, raw_path = tempfile.mkstemp(
                prefix=f"{artifact_id}-",
                suffix=".partial",
                dir=quarantine_dir,
            )
            os.close(descriptor)
            temporary_path = Path(raw_path)
            size, sha256 = await download_to_quarantine(
                client,
                source_url,
                temporary_path,
                self.limits,
                extension,
            )
            validate_artifact_content(temporary_path, extension, self.limits)

            records = self._load_manifest(project_dir)
            duplicate = next(
                (
                    record
                    for record in records
                    if record.get("sha256") == sha256
                    and record.get("status") == ArtifactStatus.VALID
                ),
                None,
            )
            if duplicate:
                return ArtifactRecord(**duplicate)

            physical_name = f"{artifact_id}{extension}"
            final_path = (project_dir / physical_name).resolve()
            final_path.relative_to(project_dir.resolve())
            if final_path.exists():
                raise ArtifactSecurityError(
                    "ARTIFACT_COLLISION",
                    "Não foi possível armazenar o arquivo com segurança.",
                )
            os.replace(temporary_path, final_path)
            temporary_path = None
            record = ArtifactRecord(
                id=artifact_id,
                original_name=original_name,
                physical_name=physical_name,
                extension=extension,
                sha256=sha256,
                size=size,
                status=ArtifactStatus.VALID,
            )
            records.append(asdict(record))
            try:
                self._save_manifest(project_dir, records)
            except OSError:
                final_path.unlink(missing_ok=True)
                raise
            return record
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)


def secure_extract_qiime_zip(
    archive_path: str | Path,
    destination: str | Path,
    limits: ArtifactLimits | None = None,
) -> Path:
    limits = limits or ArtifactLimits.from_env()
    archive_path = Path(archive_path)
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    inspect_qiime_zip(archive_path, limits)
    written = 0

    with zipfile.ZipFile(archive_path) as archive:
        for member in archive.infolist():
            target = (destination / member.filename).resolve()
            try:
                target.relative_to(destination)
            except ValueError as exc:
                raise ArtifactSecurityError(
                    "UNSAFE_ZIP_ENTRY",
                    "O artefato QIIME 2 contém uma entrada insegura.",
                ) from exc
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as source, target.open("xb") as output:
                while chunk := source.read(64 * 1024):
                    written += len(chunk)
                    if written > limits.max_uncompressed_bytes:
                        raise ArtifactSecurityError(
                            "ZIP_EXPANSION_LIMIT",
                            "O artefato QIIME 2 excede os limites de descompactação.",
                        )
                    output.write(chunk)
    return destination
