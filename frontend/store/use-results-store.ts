import { create } from 'zustand';

export interface ReportItem {
  id: string;
  type: 'plot' | 'text';
  title: string;
  base64Image?: string; // High-res image captured directly from Plotly
  textNotes?: string;   // User's manual text
}

interface ResultsState {
  alpha: any | null;
  beta: any | null;
  taxonomy: any | null;
  rarefaction: any | null;
  activeTab: string;
  reportItems: ReportItem[];
  
  setPlotData: (type: 'alpha' | 'beta' | 'taxonomy' | 'rarefaction', data: any) => void;
  setActiveTab: (tabId: string) => void;
  
  addReportItem: (item: ReportItem) => void;
  removeReportItem: (id: string) => void;
  updateReportItemText: (id: string, text: string) => void;
  clearReport: () => void;
  
  reset: () => void;
}

export const useResultsStore = create<ResultsState>((set) => ({
  alpha: null,
  beta: null,
  taxonomy: null,
  rarefaction: null,
  activeTab: 'files',
  reportItems: [],
  
  setPlotData: (type: 'alpha' | 'beta' | 'taxonomy' | 'rarefaction', data: any) => set((state: ResultsState) => ({ 
    ...state, 
    [type]: data,
    activeTab: type // Auto-switch to the newly generated plot tab
  })),
  setActiveTab: (tabId: string) => set({ activeTab: tabId }),
  
  addReportItem: (item: ReportItem) => set((state: ResultsState) => ({ reportItems: [...state.reportItems, item] })),
  removeReportItem: (id: string) => set((state: ResultsState) => ({ reportItems: state.reportItems.filter((i: ReportItem) => i.id !== id) })),
  updateReportItemText: (id: string, text: string) => set((state: ResultsState) => ({ 
    reportItems: state.reportItems.map((i: ReportItem) => i.id === id ? { ...i, textNotes: text } : i) 
  })),
  clearReport: () => set({ reportItems: [] }),
  
  reset: () => set({ alpha: null, beta: null, taxonomy: null, rarefaction: null, activeTab: 'files', reportItems: [] })
}));
