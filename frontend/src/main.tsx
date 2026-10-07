import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { Toaster } from '@/components/ui/sonner'
import { TooltipProvider } from '@/components/ui/tooltip'
import { LiveEventsProvider } from '@/hooks/useLiveEvents'
import App from './App.tsx'
import './index.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <LiveEventsProvider>
        <TooltipProvider>
          <App />
          <Toaster />
        </TooltipProvider>
      </LiveEventsProvider>
    </BrowserRouter>
  </StrictMode>,
)
