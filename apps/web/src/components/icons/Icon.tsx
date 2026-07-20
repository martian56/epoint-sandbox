import { ICON_PATHS, ICON_TRANSFORM, ICON_VIEW_BOX, type IconName } from './paths'

interface IconProps {
  name: IconName
  className?: string
  size?: number
}

export function Icon({ name, className, size = 20 }: IconProps) {
  return (
    <svg
      viewBox={ICON_VIEW_BOX}
      width={size}
      height={size}
      fill="currentColor"
      aria-hidden="true"
      focusable="false"
      className={className}
    >
      <g transform={ICON_TRANSFORM}>
        <path d={ICON_PATHS[name]} />
      </g>
    </svg>
  )
}

export type { IconName }
