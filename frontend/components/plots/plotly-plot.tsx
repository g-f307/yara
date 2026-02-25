"use client";

import dynamic from "next/dynamic";
import { useTheme } from "next-themes";
import { Skeleton } from "@/components/ui/skeleton";
import type { Layout, Data } from "plotly.js";

// Lazy load Plotly to avoid SSR issues and reduce initial bundle size
const Plot = dynamic(() => import("react-plotly.js"), {
    ssr: false,
    loading: () => (
        <div className="flex w-full items-center justify-center p-4">
            <Skeleton className="h-[400px] w-full rounded-xl" />
        </div>
    ),
});

interface PlotlyPlotProps {
    data: Data[];
    layout?: Partial<Layout>;
    title?: string;
    height?: number;
}

export function PlotlyPlot({ data, layout = {}, title, height = 400 }: PlotlyPlotProps) {
    const { theme } = useTheme();
    const isDark = theme === "dark";

    // Base theme configuration that adapts to dark/light mode
    const baseLayout: Partial<Layout> = {
        title: title ? { text: title, font: { color: isDark ? "#fff" : "#000" } } : undefined,
        autosize: true,
        height,
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        font: {
            family: "inherit",
            color: isDark ? "#a1a1aa" : "#3f3f46", // muted foreground
        },
        xaxis: {
            gridcolor: isDark ? "#27272a" : "#e4e4e7",
            zerolinecolor: isDark ? "#3f3f46" : "#d4d4d8",
            tickfont: { color: isDark ? "#a1a1aa" : "#3f3f46" },
            ...layout.xaxis,
        },
        yaxis: {
            gridcolor: isDark ? "#27272a" : "#e4e4e7",
            zerolinecolor: isDark ? "#3f3f46" : "#d4d4d8",
            tickfont: { color: isDark ? "#a1a1aa" : "#3f3f46" },
            ...layout.yaxis,
        },
        margin: { t: title ? 50 : 20, r: 20, l: 50, b: 50, ...layout.margin },
        // Merge provided layout over base layout
        ...layout,
    };

    return (
        <div className="w-full flex justify-center">
            <Plot
                data={data}
                layout={baseLayout}
                useResizeHandler={true}
                style={{ width: "100%", height: "100%" }}
                config={{
                    displayModeBar: true,
                    displaylogo: false,
                    responsive: true,
                    modeBarButtonsToRemove: ["lasso2d", "select2d"],
                }}
            />
        </div>
    );
}
