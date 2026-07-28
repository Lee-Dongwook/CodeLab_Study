import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // 0.0.0.0 바인딩 (프록시/외부 접속 허용)
    // 프록시/커스텀 도메인/터널을 거쳐 접속할 때 WebSocket(HMR) 403 방지.
    // 특정 도메인만 허용하려면 true 대신 ["example.local"] 처럼 배열로 지정.
    allowedHosts: true,
    hmr: {
      // https 프록시(wss) 뒤라면 아래 두 줄 주석 해제
      // protocol: "wss",
      // clientPort: 443,
    },
  },
});
