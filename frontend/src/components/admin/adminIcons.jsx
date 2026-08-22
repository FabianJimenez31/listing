/* Line-icon set for the admin panel (sidebar, dashboard, empty states). */
const base = { fill: 'none', stroke: 'currentColor', strokeWidth: 1.8, strokeLinecap: 'round', strokeLinejoin: 'round' }
const Svg = ({ size = 20, children }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" {...base}>{children}</svg>
)

export const IconGrid = (p) => <Svg {...p}><rect x="3" y="3" width="7" height="7" rx="1.5" /><rect x="14" y="3" width="7" height="7" rx="1.5" /><rect x="14" y="14" width="7" height="7" rx="1.5" /><rect x="3" y="14" width="7" height="7" rx="1.5" /></Svg>
export const IconHome = (p) => <Svg {...p}><path d="M3 11.5 12 4l9 7.5" /><path d="M5 10v10h14V10" /><path d="M10 20v-6h4v6" /></Svg>
export const IconPlus = (p) => <Svg {...p}><rect x="3" y="3" width="18" height="18" rx="4" /><path d="M12 8v8M8 12h8" /></Svg>
export const IconDownload = (p) => <Svg {...p}><path d="M12 4v11" /><path d="M8 11.5l4 4 4-4" /><path d="M4 19h16" /></Svg>
export const IconInbox = (p) => <Svg {...p}><path d="M3 12h5l2 3h4l2-3h5" /><path d="M5 5h14a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2z" /></Svg>
export const IconStar = (p) => <Svg {...p}><path d="M12 3.5l2.6 5.3 5.9.9-4.3 4.1 1 5.8L12 17l-5.2 2.7 1-5.8-4.3-4.1 5.9-.9z" /></Svg>
export const IconBuilding = (p) => <Svg {...p}><path d="M5 21V5a2 2 0 0 1 2-2h6a2 2 0 0 1 2 2v16" /><path d="M15 9h2a2 2 0 0 1 2 2v10" /><path d="M3 21h18M9 7h2M9 11h2M9 15h2" /></Svg>
export const IconOffice = (p) => <Svg {...p}><path d="M3 21h18M5 21V7l7-4 7 4v14" /><path d="M9 9h.01M15 9h.01M9 13h.01M15 13h.01M9 17h.01M15 17h.01" /></Svg>
export const IconUsers = (p) => <Svg {...p}><circle cx="9" cy="8" r="3.2" /><path d="M3 20a6 6 0 0 1 12 0" /><path d="M16 5.2a3.2 3.2 0 0 1 0 5.6M21 20a6 6 0 0 0-4-5.6" /></Svg>
export const IconFile = (p) => <Svg {...p}><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" /><path d="M14 3v5h5M9 13h6M9 17h6" /></Svg>
export const IconImage = (p) => <Svg {...p}><rect x="3" y="4" width="18" height="16" rx="2" /><circle cx="8.5" cy="9.5" r="1.5" /><path d="m4 18 5-5 4 4 3-3 4 4" /></Svg>
export const IconUserCog = (p) => <Svg {...p}><circle cx="9" cy="8" r="3.2" /><path d="M3 20a6 6 0 0 1 10.5-4" /><circle cx="18" cy="17" r="2.5" /><path d="M18 13v1.5M18 19.5V21M21.5 15l-1.3.75M16.8 17.25l-1.3.75M21.5 19l-1.3-.75M16.8 16.75l-1.3-.75" /></Svg>
export const IconCheckCircle = (p) => <Svg {...p}><circle cx="12" cy="12" r="9" /><path d="m8.5 12 2.5 2.5L16 9" /></Svg>
export const IconClock = (p) => <Svg {...p}><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></Svg>
export const IconTrend = (p) => <Svg {...p}><path d="M3 17l6-6 4 4 8-8" /><path d="M15 7h6v6" /></Svg>
export const IconLogout = (p) => <Svg {...p}><path d="M14 8V5a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2v-3" /><path d="M9 12h12M18 8l4 4-4 4" /></Svg>
export const IconExternal = (p) => <Svg {...p}><path d="M14 4h6v6M20 4l-9 9" /><path d="M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5" /></Svg>
export const IconMenu = (p) => <Svg {...p}><path d="M4 6h16M4 12h16M4 18h16" /></Svg>
export const IconSearchSlash = (p) => <Svg {...p}><circle cx="11" cy="11" r="7" /><path d="m21 21-4.3-4.3" /></Svg>
export const IconSettings = (p) => <Svg {...p}><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09a1.65 1.65 0 0 0 1.51-1 1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" /></Svg>
