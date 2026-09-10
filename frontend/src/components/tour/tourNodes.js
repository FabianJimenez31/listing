const DEG = Math.PI / 180

// Todas las flechas se proyectan a esta altura del piso, como Matterport.
const FLOOR_LINK_PITCH = -72 * DEG

function panoData(scene) {
  if (!scene.width || !scene.height || (scene.hfov_deg === 360 && scene.vfov_deg === 180)) return undefined
  const fullWidth = Math.round(scene.width * (360 / scene.hfov_deg))
  const fullHeight = Math.round(scene.height * (180 / scene.vfov_deg))
  return {
    fullWidth,
    fullHeight,
    croppedWidth: scene.width,
    croppedHeight: scene.height,
    croppedX: Math.round((fullWidth - scene.width) / 2),
    croppedY: Math.round((fullHeight - scene.height) / 2),
  }
}

export function buildTourNodes(ordered, hotspotsByScene) {
  const straightYaw = (sceneId, fallback) => {
    const spots = hotspotsByScene[sceneId] || []
    if (!spots.length) return fallback
    const back = Math.atan2(Math.sin(spots[0].yaw), Math.cos(spots[0].yaw))
    return back + Math.PI
  }

  return ordered.map((scene, index) => {
    const next = ordered.length > 1 ? ordered[(index + 1) % ordered.length] : null
    const nextSpot = next
      ? scene.hotspots.find((spot) => spot.to_scene_id === next.id)
      : null
    const yaw = nextSpot ? nextSpot.yaw : straightYaw(scene.id, 0)
    const links = next ? [{
      nodeId: next.id,
      position: {
        yaw: Math.atan2(Math.sin(yaw), Math.cos(yaw)),
        pitch: FLOOR_LINK_PITCH,
      },
      data: { label: nextSpot?.label || `Ir a ${next.title}` },
    }] : []

    return {
      id: scene.id,
      panorama: scene.pano_url,
      thumbnail: scene.thumb_url || scene.pano_url,
      name: scene.title,
      caption: scene.title,
      panoData: panoData(scene),
      sphereCorrection: { pan: scene.initial_yaw || 0, tilt: scene.initial_pitch || 0 },
      links,
    }
  })
}
