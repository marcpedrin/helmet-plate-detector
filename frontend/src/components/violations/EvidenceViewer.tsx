/**
 * Three-panel evidence viewer: Full Frame, Rider Crop, Plate Crop.
 * Clicking any image opens it in a full-screen Dialog.
 * Broken images show a neutral "Image unavailable" placeholder.
 *
 * @module components/violations/EvidenceViewer
 * @example
 * <EvidenceViewer violation={v} />
 */
import { useState } from 'react'
import { ImageOff, Maximize2 } from 'lucide-react'
import { Dialog, DialogContent, DialogTitle } from '@/components/ui/dialog'
import { apiUrl } from '@/services/api'
import type { ViolationOut } from '@/types/contracts'

/** Placeholder shown when an evidence image fails to load. */
const ImagePlaceholder = ({ label }: { label: string }) => (
  <div className="flex flex-col items-center justify-center gap-2 rounded-lg border border-border bg-muted/30 aspect-video text-muted-foreground">
    <ImageOff className="h-8 w-8" aria-hidden />
    <span className="text-xs">Image unavailable</span>
    <span className="text-[10px] opacity-60">{label}</span>
  </div>
)

/** One clickable evidence panel. */
const EvidencePanel = ({
  src,
  alt,
  label,
}: {
  src: string | null
  alt: string
  label: string
}) => {
  const [error, setError] = useState(false)
  const [open, setOpen] = useState(false)

  if (!src || error) return <ImagePlaceholder label={label} />

  return (
    <>
      <button
        className="group relative overflow-hidden rounded-lg border border-border bg-black cursor-zoom-in focus:outline-none focus:ring-2 focus:ring-ring"
        onClick={() => setOpen(true)}
        aria-label={`Enlarge ${alt}`}
      >
        <img
          src={apiUrl(src)}
          alt={alt}
          className="w-full object-contain max-h-64 transition-opacity group-hover:opacity-90"
          onError={() => setError(true)}
        />
        <div className="absolute top-2 right-2 rounded bg-black/60 p-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <Maximize2 className="h-3.5 w-3.5 text-white" aria-hidden />
        </div>
        <span className="absolute bottom-0 left-0 right-0 bg-black/60 px-2 py-1 text-[10px] text-white font-medium">
          {label}
        </span>
      </button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-5xl p-2 bg-black border-border">
          <DialogTitle className="sr-only">{alt}</DialogTitle>
          <img src={apiUrl(src)} alt={alt} className="w-full max-h-[90vh] object-contain rounded" />
        </DialogContent>
      </Dialog>
    </>
  )
}

/** Props for {@link EvidenceViewer}. */
export interface EvidenceViewerProps {
  /** The violation whose evidence to display. */
  violation: ViolationOut
}

/**
 * Three evidence panels: Full Frame (annotated by server), Rider Crop, Plate Crop.
 * Broken images show a placeholder. Click any image to zoom.
 *
 * @param props - See {@link EvidenceViewerProps}.
 * @returns The evidence viewer element.
 */
export const EvidenceViewer = ({ violation: v }: EvidenceViewerProps) => (
  <div className="grid gap-3 md:grid-cols-[2fr_1fr_1fr]">
    <EvidencePanel
      src={v.evidence.full_frame_url}
      alt="Full frame with detection boxes"
      label="Full Frame (annotated)"
    />
    <EvidencePanel
      src={v.evidence.rider_crop_url}
      alt="Rider crop"
      label="Rider"
    />
    <EvidencePanel
      src={v.evidence.plate_crop_url}
      alt="Number plate crop"
      label="Plate"
    />
  </div>
)
