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
    divId?: string;
}

export function PlotlyPlot({ data, layout = {}, title, height = 400, divId }: PlotlyPlotProps) {
    const { resolvedTheme } = useTheme();
    const isDark = resolvedTheme === "dark";

    // Merge layout carefully to ensure our theme colors override backend defaults
    const mergedLayout: Partial<Layout> = {
        ...layout,
        autosize: true,
        height: layout.height || height,
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        font: {
            ...layout.font,
            family: "inherit",
            color: isDark ? "#a1a1aa" : "#3f3f46",
        },
        xaxis: {
            ...layout.xaxis,
            gridcolor: isDark ? "#27272a" : "#e4e4e7",
            zerolinecolor: isDark ? "#3f3f46" : "#d4d4d8",
            tickfont: { ...(layout.xaxis as any)?.tickfont, color: isDark ? "#a1a1aa" : "#3f3f46" },
            linecolor: isDark ? "#3f3f46" : "#d4d4d8",
            title: typeof (layout.xaxis as any)?.title === 'object'
                ? { ...(layout.xaxis as any)?.title, font: { color: isDark ? "#a1a1aa" : "#3f3f46" } }
                : { text: (layout.xaxis as any)?.title, font: { color: isDark ? "#a1a1aa" : "#3f3f46" } }
        },
        yaxis: {
            ...layout.yaxis,
            gridcolor: isDark ? "#27272a" : "#e4e4e7",
            zerolinecolor: isDark ? "#3f3f46" : "#d4d4d8",
            tickfont: { ...(layout.yaxis as any)?.tickfont, color: isDark ? "#a1a1aa" : "#3f3f46" },
            linecolor: isDark ? "#3f3f46" : "#d4d4d8",
            title: typeof (layout.yaxis as any)?.title === 'object'
                ? { ...(layout.yaxis as any)?.title, font: { color: isDark ? "#a1a1aa" : "#3f3f46" } }
                : { text: (layout.yaxis as any)?.title, font: { color: isDark ? "#a1a1aa" : "#3f3f46" } }
        },
        legend: {
            ...layout.legend,
            font: { ...(layout.legend as any)?.font, color: isDark ? "#a1a1aa" : "#3f3f46" },
            bgcolor: isDark ? "rgba(24,24,27,0.8)" : "rgba(255,255,255,0.8)",
            bordercolor: isDark ? "#27272a" : "#e4e4e7",
            borderwidth: 1,
        },
        hoverlabel: {
            ...layout.hoverlabel,
            bgcolor: isDark ? "#18181b" : "#ffffff",
            bordercolor: isDark ? "#3f3f46" : "#d4d4d8",
            font: { color: isDark ? "#e4e4e7" : "#18181b" },
        },
        title: layout.title
            ? typeof layout.title === 'string'
                ? { text: layout.title, font: { color: isDark ? "#e4e4e7" : "#18181b" } }
                : { ...(layout.title as any), font: { color: isDark ? "#e4e4e7" : "#18181b" } }
            : title
                ? { text: title, font: { color: isDark ? "#e4e4e7" : "#18181b" } }
                : undefined,
        margin: { t: (layout.title || title) ? 50 : 20, r: 20, l: 50, b: 50, ...layout.margin },
    };

    return (
        <div className="w-full flex justify-center">
            <Plot
                divId={divId}
                data={data}
                layout={mergedLayout}
                useResizeHandler={true}
                style={{ width: "100%", height: "100%" }}
                config={{
                    displayModeBar: true,
                    displaylogo: false,
                    responsive: true,
                    modeBarButtonsToRemove: ["lasso2d", "select2d"],
                    // @ts-ignore — valid Plotly config options
                    modebar_bgcolor: isDark ? "rgba(24,24,27,0.6)" : "rgba(255,255,255,0.6)",
                    modebar_color: isDark ? "#a1a1aa" : "#71717a",
                    modebar_activecolor: isDark ? "#e4e4e7" : "#18181b",
                }}
            />
        </div>
    );
}

