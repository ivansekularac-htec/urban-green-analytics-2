interface ImportMetaEnv {
    readonly VITE_SUPERSET_URL: string;
    readonly VITE_GRAFANA_URL: string;
}

interface ImportMeta {
    readonly env: ImportMetaEnv;
}