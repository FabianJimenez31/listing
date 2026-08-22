import { lazy, Suspense, useState } from 'react'
import Spinner from '../ui/Spinner'
import '../../styles/tour.css'

const TourViewer = lazy(() => import('./TourViewer'))

export default function TourTab({ tour, renderPhotos }) {
  const [active, setActive] = useState('photos')
  if (!tour?.scenes?.length) return renderPhotos
  return (
    <>
      <div className="tour-media-tabs" role="tablist" aria-label="Contenido visual">
        <button type="button" className={active === 'photos' ? 'active' : ''} onClick={() => setActive('photos')}>Fotos</button>
        <button type="button" className={active === 'tour' ? 'active' : ''} onClick={() => setActive('tour')}>Tour 360</button>
      </div>
      {active === 'photos' ? renderPhotos : (
        <Suspense fallback={<div className="tour-loading"><Spinner /></div>}>
          <TourViewer tour={tour} />
        </Suspense>
      )}
    </>
  )
}
