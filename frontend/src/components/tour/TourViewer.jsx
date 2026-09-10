import { useEffect, useMemo, useRef, useState } from 'react'
import { Viewer } from '@photo-sphere-viewer/core'
import { GalleryPlugin } from '@photo-sphere-viewer/gallery-plugin'
import { MarkersPlugin } from '@photo-sphere-viewer/markers-plugin'
import { VirtualTourPlugin } from '@photo-sphere-viewer/virtual-tour-plugin'
import { buildTourNodes } from './tourNodes'
import '@photo-sphere-viewer/core/index.css'
import '@photo-sphere-viewer/gallery-plugin/index.css'
import '@photo-sphere-viewer/markers-plugin/index.css'
import '@photo-sphere-viewer/virtual-tour-plugin/index.css'
import '../../styles/tour.css'

export default function TourViewer({ tour }) {
  const shellRef = useRef(null)
  const containerRef = useRef(null)
  const viewerRef = useRef(null)
  const pluginRef = useRef(null)
  const ordered = useMemo(() => [...tour.scenes].sort((a, b) => a.position - b.position), [tour])
  // Grafo completo de hotspots por escena: la orientacion de llegada lo usa
  // aunque el visor solo muestre una flecha por escena (FR-407).
  const hotspotsByScene = useMemo(
    () => Object.fromEntries(ordered.map((scene) => [scene.id, scene.hotspots])),
    [ordered],
  )
  const initialId = tour.start_scene_id || ordered[0]?.id
  const [currentId, setCurrentId] = useState(initialId)
  const current = ordered.find((scene) => scene.id === currentId) || ordered[0]

  useEffect(() => {
    if (!ordered.length) return undefined
    // Precarga total del tour: todas las panoramicas se piden al montar para que
    // la navegacion posterior no descargue nada en vivo (FR-301/FR-302 del spec).
    const warm = ordered.map((scene) => {
      const img = new Image()
      img.decoding = 'async'
      img.src = scene.pano_url
      return img
    })
    return () => { warm.length = 0 }
  }, [ordered])

  useEffect(() => {
    if (!containerRef.current || !ordered.length) return undefined
    // Modo flecha unica (FR-407): cada escena muestra la flecha hacia la
    // siguiente. Un tour monoscena no crea links porque PSV rechaza enlaces
    // de un nodo hacia si mismo.
    const nodes = buildTourNodes(ordered, hotspotsByScene)
    const viewer = new Viewer({
      container: containerRef.current,
      navbar: ['zoom', 'move', 'fullscreen'],
      plugins: [
        MarkersPlugin,
        GalleryPlugin.withConfig({ thumbnailSize: { width: 120, height: 70 } }),
        VirtualTourPlugin.withConfig({
          nodes,
          startNodeId: initialId,
          positionMode: 'manual',
          renderMode: '3d',
          showLinkTooltip: true,
          preload: true,
          // Solo desvanecer flechas realmente superpuestas (45 por defecto
          // ocultaba salidas legitimas cercanas).
          arrowsPosition: { linkOverlapAngle: Math.PI / 8 },
          // Transicion estandar de la industria (FR-409): fundido y rotacion
          // simultaneos hacia la orientacion de llegada (opuesto a la puerta
          // de entrada), en un solo movimiento fluido. Es el mecanismo nativo
          // del plugin; sin fases ni cortes intermedios.
          transitionOptions: (node, fromNode) => {
            if (!fromNode) return {}
            const backSpot = (hotspotsByScene[node.id] || []).find(
              (spot) => spot.to_scene_id === fromNode.id,
            )
            if (!backSpot) return {}
            return {
              effect: 'fade',
              rotation: true,
              speed: '20rpm',
              rotateTo: { yaw: backSpot.yaw + Math.PI, pitch: 0 },
              zoomTo: null,
            }
          },
        }),
      ],
    })
    const plugin = viewer.getPlugin(VirtualTourPlugin)
    const onChange = ({ node }) => setCurrentId(node.id)
    plugin.addEventListener('node-changed', onChange)
    viewerRef.current = viewer
    pluginRef.current = plugin
    return () => {
      plugin.removeEventListener('node-changed', onChange)
      viewer.destroy()
      viewerRef.current = null
      pluginRef.current = null
    }
  }, [ordered, initialId, hotspotsByScene])

  const move = (direction) => {
    const index = ordered.findIndex((scene) => scene.id === currentId)
    const next = ordered[(index + direction + ordered.length) % ordered.length]
    if (next) pluginRef.current?.setCurrentNode(next.id)
  }

  const enterFullscreen = () => {
    const shell = shellRef.current
    if (shell?.requestFullscreen) shell.requestFullscreen()
    else if (shell?.webkitRequestFullscreen) shell.webkitRequestFullscreen()
  }

  return (
    <div ref={shellRef} className="tour-viewer-shell">
      <div ref={containerRef} className="tour-viewer" />
      <div className="tour-scrim" aria-hidden="true" />
      <button type="button" className="tour-fullscreen" onClick={enterFullscreen} title="Pantalla completa" aria-label="Pantalla completa">⛶</button>
      {ordered.length > 1 && (
        <div className="tour-step-controls">
          <button type="button" className="tour-step-btn" onClick={() => move(-1)} aria-label="Anterior">←</button>
          <div className="tour-step-meta">
            <strong>{current?.title}</strong>
            <span>{ordered.findIndex((scene) => scene.id === currentId) + 1} / {ordered.length}</span>
          </div>
          <button type="button" className="tour-step-btn" onClick={() => move(1)} aria-label="Siguiente">→</button>
        </div>
      )}
    </div>
  )
}
