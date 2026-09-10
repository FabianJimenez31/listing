import { useRef, useState } from 'react'
import { prioritizeMainImage } from '../../lib/imageOrder'

const Chevron = ({ dir }) => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
    {dir === 'left' ? <path d="M15 6l-6 6 6 6" /> : <path d="M9 6l6 6-6 6" />}
  </svg>
)

/**
 * Reusable image carousel with subtle slide animation, arrows, dots and counter.
 * Keyboard (←/→) and touch/drag swipe supported. Used by property & project detail.
 */
export default function ImageCarousel({ images = [], alt = '', children }) {
  const [index, setIndex] = useState(0)
  const startX = useRef(null)
  const orderedImages = prioritizeMainImage(images)
  const n = orderedImages.length

  const go = (delta) => setIndex((p) => (p + delta + n) % n)
  const to = (i) => setIndex(i)

  return (
    <div
      className="carousel"
      tabIndex={0}
      onKeyDown={(e) => { if (e.key === 'ArrowLeft') go(-1); if (e.key === 'ArrowRight') go(1) }}
      onPointerDown={(e) => { startX.current = e.clientX }}
      onPointerUp={(e) => {
        if (startX.current == null) return
        const d = e.clientX - startX.current
        if (d > 50) go(-1)
        else if (d < -50) go(1)
        startX.current = null
      }}
    >
      {children}
      <div className="carousel-track" style={{ transform: `translateX(-${index * 100}%)` }}>
        {n === 0 ? (
          <div className="carousel-slide"><div className="carousel-noimg">P</div></div>
        ) : (
          orderedImages.map((img, i) => (
            <div className="carousel-slide" key={img.id || i}>
              <img src={img.cdn_url} alt={img.alt_text || alt} loading={i === 0 ? 'eager' : 'lazy'} draggable="false" />
            </div>
          ))
        )}
      </div>

      {n > 1 && (
        <>
          <button type="button" className="carousel-arrow prev" onClick={() => go(-1)} aria-label="Anterior"><Chevron dir="left" /></button>
          <button type="button" className="carousel-arrow next" onClick={() => go(1)} aria-label="Siguiente"><Chevron dir="right" /></button>
          <div className="carousel-count">{index + 1} / {n}</div>
          <div className="carousel-dots">
            {orderedImages.map((_, i) => (
              <button type="button" key={i} className={`cdot ${i === index ? 'on' : ''}`} onClick={() => to(i)} aria-label={`Foto ${i + 1}`} />
            ))}
          </div>
        </>
      )}
    </div>
  )
}
