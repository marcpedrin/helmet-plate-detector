/**
 * Displays model load states as coloured chips in the top bar.
 *
 * States rendered:
 * - LOADED → green dot chip
 * - MOCK → blue "MOCK" chip
 * - NOT_LOADED / ERROR → red "MODEL NOT LOADED" chip with tooltip showing the model name
 *
 * @module components/layout/ModelStatus
 * @example
 * <ModelStatus health={health} />
 */
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import type { HealthOut, ModelState } from '@/types/contracts'

/** Display names for each model key. */
const MODEL_LABELS: Record<keyof HealthOut['models'], string> = {
  detector: 'Detector',
  helmet: 'Helmet',
  plate_detector: 'Plate',
  ocr: 'OCR',
}

/**
 * One model chip props.
 *
 * @param name - Short label.
 * @param state - Model load state.
 */
const ModelChip = ({ name, state }: { name: string; state: ModelState }) => {
  if (state === 'LOADED') {
    return (
      <span className="flex items-center gap-1 rounded px-1.5 py-0.5 text-xs bg-online/20 text-online border border-online">
        <span className="h-1.5 w-1.5 rounded-full bg-online" />
        {name}
      </span>
    )
  }
  if (state === 'MOCK') {
    return (
      <span className="flex items-center gap-1 rounded px-1.5 py-0.5 text-xs bg-mock/10 text-mock border border-mock/30"
        style={{ '--mock': 'var(--mock-accent)' } as React.CSSProperties}>
        <span className="h-1.5 w-1.5 rounded-full" style={{ background: 'var(--mock-accent)' }} />
        {name}
        <span className="opacity-70">MOCK</span>
      </span>
    )
  }
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span className="flex items-center gap-1 rounded px-1.5 py-0.5 text-xs bg-offline/20 text-offline border border-offline cursor-help">
          <span className="h-1.5 w-1.5 rounded-full bg-offline" />
          {name}
          <span className="font-semibold">MODEL NOT LOADED</span>
        </span>
      </TooltipTrigger>
      <TooltipContent>
        <p>{MODEL_LABELS[name as keyof typeof MODEL_LABELS] ?? name} is {state}</p>
      </TooltipContent>
    </Tooltip>
  )
}

/**
 * Renders four model-state chips (Detector, Helmet, Plate, OCR).
 *
 * @param props.health - Current health response; if null, shows skeleton chips.
 * @returns Model status chips.
 */
export const ModelStatus = ({ health }: { health: HealthOut | null }) => {
  if (!health) {
    return (
      <div className="flex gap-1.5">
        {(['Detector', 'Helmet', 'Plate', 'OCR'] as const).map((n) => (
          <span key={n} className="h-5 w-16 rounded bg-muted animate-pulse" />
        ))}
      </div>
    )
  }
  return (
    <div className="flex flex-wrap gap-1.5">
      {(Object.entries(health.models) as [keyof HealthOut['models'], ModelState][]).map(([key, state]) => (
        <ModelChip key={key} name={MODEL_LABELS[key]} state={state} />
      ))}
    </div>
  )
}
