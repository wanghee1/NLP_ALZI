import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// 프론트는 VITE_API_BASE_URL 절대주소로 백엔드를 직접 호출하고
// 백엔드 CORS 로 허용한다. 따라서 dev 프록시는 두지 않는다.
export default defineConfig({
  plugins: [react()],
  server: { port: 5173 },
})
