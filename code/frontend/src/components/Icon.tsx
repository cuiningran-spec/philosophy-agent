const PATHS: Record<string, string[]> = {
  'arrow-up-right': ['M7 17 17 7', 'M7 7h10v10'],
  'arrow-down-right': ['m7 7 10 10', 'M17 7v10H7'],
  'arrow-right': ['M5 12h14', 'm12 5 7 7-7 7'],
  'arrow-up': ['m5 12 7-7 7 7', 'M12 19V5'],
  'arrow-left': ['M19 12H5', 'm12 19-7-7 7-7'],
  check: ['M20 6 9 17l-5-5'],
  compass: ['M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20Z', 'm16.2 7.8-2.1 6.3-6.3 2.1 2.1-6.3 6.3-2.1Z'],
  columns: ['M3 3h18v18H3z', 'M9 3v18', 'M15 3v18'],
  waves: ['M2 8c2.5 0 2.5 2 5 2s2.5-2 5-2 2.5 2 5 2 2.5-2 5-2', 'M2 16c2.5 0 2.5 2 5 2s2.5-2 5-2 2.5 2 5 2 2.5-2 5-2'],
  quote: ['M9 7H5a2 2 0 0 0-2 2v3a2 2 0 0 0 2 2h2v1a3 3 0 0 1-3 3', 'M20 7h-4a2 2 0 0 0-2 2v3a2 2 0 0 0 2 2h2v1a3 3 0 0 1-3 3'],
  scroll: ['M5 4h14v16H5z', 'M8 9h8', 'M8 13h8', 'M8 17h5'],
  bookmark: ['m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z'],
  glasses: ['M2 14a4 4 0 1 0 8 0 4 4 0 1 0-8 0', 'M14 14a4 4 0 1 0 8 0 4 4 0 1 0-8 0', 'M10 14h4', 'm2 12 2-5', 'm22 12-2-5'],
  messages: ['M14 9a2 2 0 0 1-2 2H6l-4 4V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2z', 'M18 9h2a2 2 0 0 1 2 2v11l-4-4h-6a2 2 0 0 1-2-2v-1'],
  pen: ['M12 20h9', 'M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z'],
  sparkles: ['m12 3 1.9 5.8L20 10l-6.1 1.2L12 17l-1.9-5.8L4 10l6.1-1.2z', 'M19 15l.8 2.4L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.6z'],
  search: ['M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16Z', 'm21 21-4.3-4.3'],
  replace: ['M14 4a8 8 0 0 1 6 12.9', 'M16 20a8 8 0 0 1-14-8.9', 'M2 4v6h6', 'M22 20v-6h-6'],
  refresh: ['M3 12a9 9 0 0 1 15-6.7L21 8', 'M21 3v5h-5', 'M21 12a9 9 0 0 1-15 6.7L3 16', 'M3 21v-5h5'],
  shield: ['M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z', 'm9 12 2 2 4-4'],
  lock: ['M5 11h14v10H5z', 'M8 11V7a4 4 0 0 1 8 0v4'],
  info: ['M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Z', 'M12 8h.01', 'M11 12h1v5h1'],
  fork: ['M6 3v12', 'M6 21a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z', 'M18 9a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z', 'M18 9v3a3 3 0 0 1-3 3H9'],
  list: ['M8 6h13', 'M8 12h13', 'M8 18h13', 'M3 6h.01', 'M3 12h.01', 'M3 18h.01'],
}

export type IconName = keyof typeof PATHS

interface IconProps {
  name: IconName
  size?: number
  className?: string
  strokeWidth?: number
}

export function Icon({ name, size = 16, className, strokeWidth = 1.6 }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      {(PATHS[name] || []).map((d) => (
        <path key={d} d={d} />
      ))}
    </svg>
  )
}
