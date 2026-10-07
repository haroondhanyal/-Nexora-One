import type { ComponentType } from "react";

export type Row = { id: string; [key: string]: string };
export type Store = Record<string, Row[]>;
export type Module = { key: string; label: string; phase: 1 | 2 | 3 | 4 | 5; group: string; icon: ComponentType<{size?: number}>; fields: string[]; columns: string[] };
