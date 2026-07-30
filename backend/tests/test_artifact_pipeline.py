from __future__ import annotations

import asyncio
import hashlib
import json
import os
import stat
import tempfile
import unittest
import uuid
import zipfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx

from security.artifact_pipeline import (
    ArtifactLimits,
    ArtifactSecurityError,
    ArtifactStore,
    download_to_quarantine,
    inspect_qiime_zip,
    normalize_project_id,
    read_file_prefix,
    safe_project_dir,
    secure_extract_qiime_zip,
    validate_artifact_content,
    validate_artifact_configuration,
    validate_declared_mime,
    validate_original_name,
    validate_remote_url,
)
from routers.qc import QCRequest, qc_summary
from utils.project_manager import ProjectManager, _PROJECT_LOCKS, _project_lock


def limits(**overrides) -> ArtifactLimits:
    values = {
        "max_download_bytes": 1024,
        "max_zip_entries": 20,
        "max_uncompressed_bytes": 4096,
        "max_compression_ratio": 100.0,
        "max_redirects": 2,
        "connect_timeout_seconds": 1.0,
        "read_timeout_seconds": 1.0,
    }
    values.update(overrides)
    return ArtifactLimits(**values)


def write_qiime_archive(
    path: Path,
    *,
    extension: str = ".qza",
    table: bytes = b"sample\tvalue\ns1\t1\n",
) -> Path:
    archive_path = path.with_suffix(extension)
    root = "11111111-1111-1111-1111-111111111111"
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(f"{root}/VERSION", "QIIME 2\narchive: 5\nframework: 2024.2.0\n")
        archive.writestr(f"{root}/metadata.yaml", "type: FeatureData[Table]\n")
        archive.writestr(f"{root}/data/table.tsv", table)
    return archive_path


class ArtifactPathTests(unittest.TestCase):
    def test_invalid_limits_fail_configuration(self):
        with patch.dict(os.environ, {"MAX_FILE_SIZE_BYTES": "0"}):
            with self.assertRaises(RuntimeError):
                validate_artifact_configuration()

    def test_project_id_must_be_canonical_uuid(self):
        project_id = str(uuid.uuid4())
        self.assertEqual(normalize_project_id(project_id), project_id)
        for invalid in ("../outside", "/tmp/project", "not-a-uuid"):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ArtifactSecurityError):
                    normalize_project_id(invalid)

    def test_project_path_stays_inside_storage(self):
        with tempfile.TemporaryDirectory() as temporary:
            project_id = str(uuid.uuid4())
            target = safe_project_dir(temporary, project_id)
            target.relative_to(Path(temporary).resolve())

    def test_original_name_is_metadata_not_a_path(self):
        for unsafe in ("../sample.tsv", "/tmp/sample.tsv", r"..\sample.tsv", "a/b.tsv"):
            with self.subTest(unsafe=unsafe):
                with self.assertRaises(ArtifactSecurityError):
                    validate_original_name(unsafe)
        self.assertEqual(validate_original_name("sample.tsv")[1], ".tsv")


class ArtifactUrlTests(unittest.IsolatedAsyncioTestCase):
    async def test_localhost_and_private_network_are_rejected(self):
        with patch.dict(
            os.environ,
            {
                "ENVIRONMENT": "development",
                "ALLOWED_STORAGE_HOSTS": "localhost,127.0.0.1,10.0.0.1",
            },
        ):
            for url in (
                "http://localhost/file.tsv",
                "http://127.0.0.1/file.tsv",
                "http://10.0.0.1/file.tsv",
            ):
                with self.subTest(url=url):
                    with self.assertRaises(ArtifactSecurityError):
                        await validate_remote_url(url)

    async def test_non_https_scheme_is_rejected_in_production(self):
        with patch.dict(
            os.environ,
            {
                "ENVIRONMENT": "production",
                "ALLOWED_STORAGE_HOSTS": "files.example",
            },
        ):
            with self.assertRaises(ArtifactSecurityError) as context:
                await validate_remote_url("http://files.example/data.tsv")
        self.assertEqual(context.exception.code, "URL_SCHEME_BLOCKED")

    async def test_authorized_public_host_is_resolved(self):
        with (
            patch.dict(
                os.environ,
                {
                    "ENVIRONMENT": "production",
                    "ALLOWED_STORAGE_HOSTS": "files.example",
                },
            ),
            patch(
                "security.artifact_pipeline.resolve_public_addresses",
                new_callable=AsyncMock,
                return_value={"203.0.113.10"},
            ) as resolver,
        ):
            await validate_remote_url("https://files.example/data.tsv")
        resolver.assert_awaited_once()

    async def test_redirect_to_private_network_is_rejected(self):
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                302,
                headers={"location": "http://127.0.0.1/internal"},
                request=request,
            )

        with (
            tempfile.TemporaryDirectory() as temporary,
            patch.dict(
                os.environ,
                {
                    "ENVIRONMENT": "development",
                    "ALLOWED_STORAGE_HOSTS": "files.example,127.0.0.1",
                },
            ),
            patch(
                "security.artifact_pipeline.resolve_public_addresses",
                new_callable=AsyncMock,
                return_value={"93.184.216.34"},
            ),
        ):
            destination = Path(temporary) / "download.partial"
            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
                with self.assertRaises(ArtifactSecurityError) as context:
                    await download_to_quarantine(
                        client,
                        "http://files.example/data.tsv",
                        destination,
                        limits(),
                    )
        self.assertEqual(context.exception.code, "URL_PRIVATE_ADDRESS")


class ArtifactContentTests(unittest.TestCase):
    def test_prefix_reader_returns_only_requested_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "large.bin"
            path.write_bytes(b"A" * (1024 * 1024))
            self.assertEqual(read_file_prefix(path, 16), b"A" * 16)
            self.assertEqual(len(read_file_prefix(path, 4096)), 4096)

    def test_empty_and_false_extension_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            empty = Path(temporary) / "empty.tsv"
            empty.write_bytes(b"")
            html = Path(temporary) / "page.tsv"
            html.write_bytes(b"<!doctype html><html></html>")
            with self.assertRaises(ArtifactSecurityError):
                validate_artifact_content(empty, ".tsv", limits())
            with self.assertRaises(ArtifactSecurityError):
                validate_artifact_content(html, ".tsv", limits())

    def test_valid_tsv_is_accepted(self):
        with tempfile.TemporaryDirectory() as temporary:
            table = Path(temporary) / "table.tsv"
            table.write_text("sample\tvalue\ns1\t1\n", encoding="utf-8")
            validate_artifact_content(table, ".tsv", limits())

    def test_incompatible_declared_mime_is_rejected(self):
        with self.assertRaises(ArtifactSecurityError) as context:
            validate_declared_mime("text/html; charset=utf-8", ".tsv")
        self.assertEqual(context.exception.code, "MIME_TYPE_MISMATCH")

    def test_valid_qza_and_qzv_are_accepted(self):
        with tempfile.TemporaryDirectory() as temporary:
            for extension in (".qza", ".qzv"):
                archive = write_qiime_archive(Path(temporary) / "artifact", extension=extension)
                validate_artifact_content(archive, extension, limits())

    def test_zip_slip_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            archive = Path(temporary) / "slip.qza"
            with zipfile.ZipFile(archive, "w") as output:
                output.writestr("../outside.tsv", "sample\tvalue\ns1\t1\n")
            with self.assertRaises(ArtifactSecurityError) as context:
                inspect_qiime_zip(archive, limits())
        self.assertEqual(context.exception.code, "UNSAFE_ZIP_ENTRY")

    def test_zip_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            archive = Path(temporary) / "symlink.qza"
            root = "11111111-1111-1111-1111-111111111111"
            link = zipfile.ZipInfo(f"{root}/data/link")
            link.create_system = 3
            link.external_attr = (stat.S_IFLNK | 0o777) << 16
            with zipfile.ZipFile(archive, "w") as output:
                output.writestr(f"{root}/VERSION", "QIIME 2")
                output.writestr(f"{root}/metadata.yaml", "type: Test")
                output.writestr(link, "../../outside")
            with self.assertRaises(ArtifactSecurityError) as context:
                inspect_qiime_zip(archive, limits())
        self.assertEqual(context.exception.code, "UNSAFE_ZIP_ENTRY")

    def test_controlled_zip_bomb_is_rejected_by_ratio(self):
        with tempfile.TemporaryDirectory() as temporary:
            archive = write_qiime_archive(
                Path(temporary) / "compressed",
                table=b"A" * 2048,
            )
            with self.assertRaises(ArtifactSecurityError) as context:
                inspect_qiime_zip(
                    archive,
                    limits(
                        max_uncompressed_bytes=10_000,
                        max_compression_ratio=2.0,
                    ),
                )
        self.assertEqual(context.exception.code, "ZIP_EXPANSION_LIMIT")

    def test_secure_extraction_keeps_files_inside_destination(self):
        with tempfile.TemporaryDirectory() as temporary:
            archive = write_qiime_archive(Path(temporary) / "valid")
            destination = Path(temporary) / "extracted"
            secure_extract_qiime_zip(archive, destination, limits())
            for path in destination.rglob("*"):
                path.resolve().relative_to(destination.resolve())


class ArtifactDownloadTests(unittest.IsolatedAsyncioTestCase):
    async def test_existing_quarantine_permissions_are_hardened(self):
        with tempfile.TemporaryDirectory() as temporary:
            project_id = str(uuid.uuid4())
            quarantine = Path(temporary) / project_id / ".quarantine"
            quarantine.mkdir(parents=True)
            quarantine.chmod(0o777)
            store = ArtifactStore(temporary)
            async with httpx.AsyncClient() as client:
                with self.assertRaises(ArtifactSecurityError):
                    await store.sync_one(
                        client,
                        project_id,
                        "https://files.example/data.tsv",
                        "../unsafe.tsv",
                    )
            self.assertEqual(stat.S_IMODE(quarantine.stat().st_mode), 0o700)

    async def test_streaming_download_stops_at_limit(self):
        payload = b"x" * 2048

        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, content=payload, request=request)

        with (
            tempfile.TemporaryDirectory() as temporary,
            patch(
                "security.artifact_pipeline.validate_remote_url",
                new_callable=AsyncMock,
            ),
        ):
            destination = Path(temporary) / "large.partial"
            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
                with self.assertRaises(ArtifactSecurityError) as context:
                    await download_to_quarantine(
                        client,
                        "https://files.example/large.tsv",
                        destination,
                        limits(max_download_bytes=1024),
                    )
        self.assertEqual(context.exception.code, "DOWNLOAD_SIZE_LIMIT")

    async def test_valid_artifact_is_promoted_with_uuid_hash_and_manifest(self):
        payload = b"sample\tvalue\ns1\t1\n"

        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, content=payload, request=request)

        with (
            tempfile.TemporaryDirectory() as temporary,
            patch.dict(
                os.environ,
                {
                    "MAX_FILE_SIZE_BYTES": "1024",
                    "ALLOWED_STORAGE_HOSTS": "files.example",
                },
            ),
            patch(
                "security.artifact_pipeline.validate_remote_url",
                new_callable=AsyncMock,
            ),
        ):
            project_id = str(uuid.uuid4())
            store = ArtifactStore(temporary)
            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
                record = await store.sync_one(
                    client,
                    project_id,
                    "https://files.example/table.tsv",
                    "table.tsv",
                )

            project_dir = Path(temporary) / project_id
            physical = project_dir / record.physical_name
            manifest = json.loads(
                (project_dir / ".artifacts.json").read_text(encoding="utf-8")
            )
            self.assertTrue(physical.is_file())
            self.assertEqual(record.status, "VALID")
            self.assertEqual(record.sha256, hashlib.sha256(payload).hexdigest())
            self.assertEqual(record.size, len(payload))
            self.assertEqual(manifest[0]["sha256"], record.sha256)
            self.assertTrue(uuid.UUID(Path(record.physical_name).stem))
            self.assertEqual(list((project_dir / ".quarantine").iterdir()), [])

    async def test_rejected_artifact_is_not_promoted_or_left_partial(self):
        payload = b"<!doctype html><html></html>"

        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, content=payload, request=request)

        with (
            tempfile.TemporaryDirectory() as temporary,
            patch.dict(os.environ, {"MAX_FILE_SIZE_BYTES": "1024"}),
            patch(
                "security.artifact_pipeline.validate_remote_url",
                new_callable=AsyncMock,
            ),
        ):
            project_id = str(uuid.uuid4())
            store = ArtifactStore(temporary)
            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
                with self.assertRaises(ArtifactSecurityError):
                    await store.sync_one(
                        client,
                        project_id,
                        "https://files.example/page.tsv",
                        "page.tsv",
                    )
            project_dir = Path(temporary) / project_id
            promoted = [
                path
                for path in project_dir.iterdir()
                if path.is_file() and not path.name.startswith(".")
            ]
            self.assertEqual(promoted, [])
            self.assertEqual(list((project_dir / ".quarantine").iterdir()), [])


class ArtifactAnalysisVisibilityTests(unittest.TestCase):
    def test_unregistered_file_is_not_visible_to_analyses(self):
        with tempfile.TemporaryDirectory() as temporary:
            project_id = str(uuid.uuid4())
            project_dir = Path(temporary) / project_id
            project_dir.mkdir()
            (project_dir / "untrusted.tsv").write_text(
                "sample\tvalue\ns1\t1\n",
                encoding="utf-8",
            )
            with patch("utils.project_manager.CACHE_DIR", temporary):
                self.assertEqual(
                    ProjectManager._valid_files(project_id, {".tsv"}),
                    [],
                )


class QCArtifactVisibilityTests(unittest.IsolatedAsyncioTestCase):
    async def test_qc_ignores_unregistered_table(self):
        with tempfile.TemporaryDirectory() as temporary:
            project_id = str(uuid.uuid4())
            project_dir = Path(temporary) / project_id
            project_dir.mkdir()
            (project_dir / "untrusted.tsv").write_text(
                "sample-id\treads\ns1\t1000\n",
                encoding="utf-8",
            )
            with patch("utils.project_manager.CACHE_DIR", temporary):
                response = await qc_summary(QCRequest(project_id=project_id))
            self.assertIn("error", response)
            self.assertNotIn("data", response)

    async def test_qc_uses_registered_valid_table(self):
        with tempfile.TemporaryDirectory() as temporary:
            project_id = str(uuid.uuid4())
            source = Path(temporary) / "qc.tsv"
            source.write_text(
                "sample-id\treads\ns1\t1000\ns2\t2000\n",
                encoding="utf-8",
            )
            ArtifactStore(temporary).import_local_validated(
                project_id,
                source,
                source.name,
            )
            with patch("utils.project_manager.CACHE_DIR", temporary):
                response = await qc_summary(QCRequest(project_id=project_id))
            self.assertEqual(response["data"]["total_samples"], 2)
            self.assertEqual(response["data"]["total_reads"], 3000)


class ProjectLockRegistryTests(unittest.IsolatedAsyncioTestCase):
    async def test_project_lock_is_removed_after_last_reference(self):
        project_id = str(uuid.uuid4())
        async with _project_lock(project_id):
            self.assertIn(project_id, _PROJECT_LOCKS)
        self.assertNotIn(project_id, _PROJECT_LOCKS)

    async def test_waiters_share_one_lock_without_early_eviction(self):
        project_id = str(uuid.uuid4())
        first_entered = asyncio.Event()
        release_first = asyncio.Event()
        second_entered = asyncio.Event()

        async def first():
            async with _project_lock(project_id):
                first_entered.set()
                await release_first.wait()

        async def second():
            await first_entered.wait()
            async with _project_lock(project_id):
                second_entered.set()

        first_task = asyncio.create_task(first())
        second_task = asyncio.create_task(second())
        await first_entered.wait()
        await asyncio.sleep(0)
        self.assertFalse(second_entered.is_set())
        self.assertEqual(_PROJECT_LOCKS[project_id][1], 2)
        release_first.set()
        await asyncio.gather(first_task, second_task)
        self.assertNotIn(project_id, _PROJECT_LOCKS)


if __name__ == "__main__":
    unittest.main()
