import { useEffect, useState } from 'react'
import { Helmet } from 'react-helmet-async'
import { searchProperties } from '../api/properties'
import HeroSection from '../components/home/HeroSection'
import CategoryPills from '../components/home/CategoryPills'
import FeaturedListings from '../components/home/FeaturedListings'
import CitiesSection from '../components/home/CitiesSection'
import ValueSection from '../components/home/ValueSection'
import AlliesSection from '../components/home/AlliesSection'
import AppPromoSection from '../components/home/AppPromoSection'

export default function HomePage() {
  const [properties, setProperties] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Properties flagged "Mostrar en portada" (published only — the API enforces it)
    searchProperties({ on_home: true, page_size: 12 })
      .then((res) => setProperties(res.data || []))
      .catch(() => setProperties([]))
      .finally(() => setLoading(false))
  }, [])

  return (
    <>
      <Helmet>
        <title>Proppietario — Venta, Arriendo y Proyectos en Colombia y USA</title>
        <meta
          name="description"
          content="Venta, arriendo y proyectos en Colombia y Estados Unidos. Encuentra propiedades de inversión en Bogotá, Medellín, Miami, Austin y más ciudades."
        />
      </Helmet>

      <HeroSection />
      <CategoryPills />
      <FeaturedListings items={properties} loading={loading} />
      <CitiesSection />
      <ValueSection />
      <AlliesSection />
      <AppPromoSection />
    </>
  )
}
