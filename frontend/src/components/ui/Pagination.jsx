export default function Pagination({ meta, onPage }) {
  if (!meta || meta.total_pages <= 1) return null

  const pages = Array.from({ length: meta.total_pages }, (_, i) => i + 1)

  return (
    <div style={{ display: 'flex', gap: 8, justifyContent: 'center', marginTop: '2rem', flexWrap: 'wrap' }}>
      {pages.map((p) => (
        <button
          key={p}
          onClick={() => onPage(p)}
          style={{
            padding: '8px 14px',
            borderRadius: 8,
            border: p === meta.page ? 'none' : '1px solid #DDE8FF',
            background: p === meta.page ? '#0251FD' : '#fff',
            color: p === meta.page ? '#fff' : '#4A5680',
            cursor: 'pointer',
            fontWeight: p === meta.page ? 700 : 400,
            fontFamily: "'Montserrat', sans-serif",
            fontSize: 14,
            transition: 'all 150ms',
          }}
        >
          {p}
        </button>
      ))}
    </div>
  )
}
