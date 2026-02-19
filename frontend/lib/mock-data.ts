export interface Project {
  id: string
  name: string
  date: string
  fileType: ".tsv" | ".qzv" | ".qza" | ".biom"
  fileCount: number
  analysisCount: number
}

export interface ChatMessage {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: string
  analysisCard?: AnalysisCardData
}

export interface AnalysisCardData {
  metricName: string
  value: string
  pValue?: string
  interpretation: "success" | "warning" | "danger" | "info"
  interpretationLabel: string
  stats?: { label: string; value: string }[]
}

export interface UploadedFile {
  id: string
  name: string
  type: string
  size: string
  uploadDate: string
}

export interface AnalysisHistory {
  id: string
  name: string
  timestamp: string
  summary: string
}

export const mockProjects: Project[] = [
  {
    id: "amazonia-solo",
    name: "Amazonia Solo",
    date: "Jun 2025",
    fileType: ".qzv",
    fileCount: 4,
    analysisCount: 3,
  },
  {
    id: "rio-negro-sediment",
    name: "Rio Negro Sediment",
    date: "May 2025",
    fileType: ".tsv",
    fileCount: 2,
    analysisCount: 1,
  },
  {
    id: "inpa-microbiome",
    name: "INPA Microbiome Study",
    date: "Apr 2025",
    fileType: ".biom",
    fileCount: 8,
    analysisCount: 7,
  },
]

export const mockMessages: ChatMessage[] = [
  {
    id: "1",
    role: "user",
    content: "Quais dados tenho disponiveis neste projeto?",
    timestamp: "10:23 AM",
  },
  {
    id: "2",
    role: "assistant",
    content:
      "Your project contains alpha diversity data for **15 samples** collected from soil sites in the Amazon Basin. The dataset includes three key diversity metrics:\n\n- **Shannon Index** — measures species richness and evenness\n- **Simpson Index** — probability that two randomly selected individuals belong to different species\n- **Observed Features** — total number of unique ASVs detected\n\nI ran a preliminary comparison between the two sample groups (forest vs. cleared). Here are the key findings:",
    timestamp: "10:23 AM",
    analysisCard: {
      metricName: "Shannon Diversity Index",
      value: "3.24",
      pValue: "0.032",
      interpretation: "success",
      interpretationLabel: "Significant difference between groups",
      stats: [
        { label: "Mean (Forest)", value: "3.81" },
        { label: "Mean (Cleared)", value: "2.67" },
        { label: "Std Dev", value: "0.42" },
        { label: "Test", value: "Mann-Whitney U" },
      ],
    },
  },
  {
    id: "3",
    role: "user",
    content: "Gera o grafico de PCoA",
    timestamp: "10:25 AM",
  },
  {
    id: "4",
    role: "assistant",
    content:
      "I generated a PCoA ordination plot using **Bray-Curtis** dissimilarity. The first two axes explain **42.3%** and **18.7%** of the total variance respectively.\n\nThe plot is now available in the Results panel on the right. Forest samples cluster tightly together, while cleared-area samples show higher dispersion — consistent with the alpha diversity findings.",
    timestamp: "10:25 AM",
  },
]

export const mockFiles: UploadedFile[] = [
  {
    id: "f1",
    name: "alpha_diversity.qzv",
    type: ".qzv",
    size: "2.4 MB",
    uploadDate: "Jun 12, 2025",
  },
  {
    id: "f2",
    name: "feature_table.biom",
    type: ".biom",
    size: "8.1 MB",
    uploadDate: "Jun 12, 2025",
  },
  {
    id: "f3",
    name: "metadata.tsv",
    type: ".tsv",
    size: "24 KB",
    uploadDate: "Jun 12, 2025",
  },
  {
    id: "f4",
    name: "taxonomy.qza",
    type: ".qza",
    size: "1.7 MB",
    uploadDate: "Jun 13, 2025",
  },
]

export const mockHistory: AnalysisHistory[] = [
  {
    id: "h1",
    name: "Alpha Diversity Analysis",
    timestamp: "Jun 12, 2025 — 10:23 AM",
    summary: "Shannon, Simpson, Observed Features for 15 samples. Significant difference found (p=0.032).",
  },
  {
    id: "h2",
    name: "PCoA Ordination — Bray-Curtis",
    timestamp: "Jun 12, 2025 — 10:25 AM",
    summary: "2D PCoA plot. Axis 1: 42.3%, Axis 2: 18.7%. Clear group separation.",
  },
  {
    id: "h3",
    name: "Taxonomic Bar Plot",
    timestamp: "Jun 13, 2025 — 2:15 PM",
    summary: "Phylum-level composition across all 15 samples. Proteobacteria dominant.",
  },
]

export const suggestionChips = [
  "Analyze alpha diversity",
  "Compare groups",
  "Generate PCoA plot",
  "Generate report",
]
