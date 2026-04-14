import { create } from 'zustand';

export interface ReportItem {
  id: string;
  type: 'plot' | 'text';
  title: string;
  base64Image?: string; // High-res image captured directly from Plotly
  textNotes?: string;   // User's manual text
}

const PLOT_LABELS: Record<string, string> = {
  qc: 'QC',
  alpha: 'Alpha Diversity',
  beta: 'PCoA',
  taxonomy: 'Taxonomy',
  rarefaction: 'Rarefaction',
  statistics: 'Statistics',
};

interface ResultsState {
  qc: any | null;
  alpha: any | null;
  beta: any | null;
  taxonomy: any | null;
  rarefaction: any | null;
  statistics: any | null;
  activeTab: string;
  reportItems: ReportItem[];
  pendingNotifications: Array<{ type: string; label: string }>;
  
  setPlotData: (type: 'qc' | 'alpha' | 'beta' | 'taxonomy' | 'rarefaction' | 'statistics', data: any) => void;
  setActiveTab: (tabId: string) => void;
  clearNotifications: () => void;
  
  addReportItem: (item: ReportItem) => void;
  removeReportItem: (id: string) => void;
  updateReportItemText: (id: string, text: string) => void;
  clearReport: () => void;
  
  reset: () => void;
}

export const useResultsStore = create<ResultsState>((set) => ({
  qc: null,
  alpha: null,
  beta: null,
  taxonomy: null,
  rarefaction: null,
  statistics: null,
  activeTab: 'files',
  reportItems: [],
  pendingNotifications: [],
  
  setPlotData: (type: 'qc' | 'alpha' | 'beta' | 'taxonomy' | 'rarefaction' | 'statistics', data: any) => set((state: ResultsState) => ({
    ...state, 
    [type]: data,
    pendingNotifications: [
      ...state.pendingNotifications.filter((notification) => notification.type !== type),
      { type, label: PLOT_LABELS[type] },
    ],
  })),
  setActiveTab: (tabId: string) => set({ activeTab: tabId }),
  clearNotifications: () => set({ pendingNotifications: [] }),
  
  addReportItem: (item: ReportItem) => set((state: ResultsState) => ({ reportItems: [...state.reportItems, item] })),
  removeReportItem: (id: string) => set((state: ResultsState) => ({ reportItems: state.reportItems.filter((i: ReportItem) => i.id !== id) })),
  updateReportItemText: (id: string, text: string) => set((state: ResultsState) => ({ 
    reportItems: state.reportItems.map((i: ReportItem) => i.id === id ? { ...i, textNotes: text } : i) 
  })),
  clearReport: () => set({ reportItems: [] }),
  
  reset: () => set({ qc: null, alpha: null, beta: null, taxonomy: null, rarefaction: null, statistics: null, activeTab: 'files', reportItems: [], pendingNotifications: [] })
}));
