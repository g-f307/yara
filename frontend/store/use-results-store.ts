import { create } from 'zustand';

interface ResultsState {
  alpha: any | null;
  beta: any | null;
  taxonomy: any | null;
  rarefaction: any | null;
  activeTab: string;
  setPlotData: (type: 'alpha' | 'beta' | 'taxonomy' | 'rarefaction', data: any) => void;
  setActiveTab: (tabId: string) => void;
  reset: () => void;
}

export const useResultsStore = create<ResultsState>((set) => ({
  alpha: null,
  beta: null,
  taxonomy: null,
  rarefaction: null,
  activeTab: 'files',
  setPlotData: (type: 'alpha' | 'beta' | 'taxonomy' | 'rarefaction', data: any) => set((state: ResultsState) => ({ 
    ...state, 
    [type]: data,
    activeTab: type // Auto-switch to the newly generated plot tab
  })),
  setActiveTab: (tabId: string) => set({ activeTab: tabId }),
  reset: () => set({ alpha: null, beta: null, taxonomy: null, rarefaction: null, activeTab: 'files' })
}));
