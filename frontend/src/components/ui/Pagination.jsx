export default function Pagination({ meta, onPage }) {
  if (!meta || meta.total_pages <= 1) return null

  const pages = Array.from({ length: meta.total_pages }, (_, i) => i + 1)

  return (
    <div style={{ display: 'flex', gap: 8, justifyContent: 'center', marginTop: '2rem' }}>
      {pages.map((p) => (
        <button
          key={p}
          onClick={() => onPage(p)}
          style={{
            padding: '6px 12px',
            borderRadius: 6,
            border: '1px solid #ddd',
            background: p === meta.page ? '#e94560' : '#fff',
            color: p === meta.page ? '#fff' : '#333',
            cursor: 'pointer',
            fontWeight: p === meta.page ? 700 : 400,
          }}
        >
          {p}
        </button>
      ))}
    </div>
  )
}
