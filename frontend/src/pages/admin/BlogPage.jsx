import { useEffect, useState } from 'react'
import { Helmet } from 'react-helmet-async'
import { useAuth } from '../../contexts/AuthContext'
import { createPost, deletePost, getPosts, updatePost } from '../../api/blog'
import AdminPageHeader from '../../components/admin/AdminPageHeader'
import { IconFile } from '../../components/admin/adminIcons'
import Spinner from '../../components/ui/Spinner'

const EMPTY = { title: '', category: '', excerpt: '', cover_image_url: '', content: '', status: 'draft' }

export default function AdminBlogPage() {
  const { user } = useAuth()
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [form, setForm] = useState(EMPTY)
  const [editId, setEditId] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  const load = () => {
    setLoading(true)
    getPosts({ status: 'all', page_size: 50 })
      .then((r) => setItems(r.data || []))
      .catch(() => setItems([]))
      .finally(() => setLoading(false))
  }

  useEffect(() => { if (user) load() }, [user])

  const upd = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))
  const startNew = () => { setForm(EMPTY); setEditId(null); setShowForm(true) }
  const startEdit = (p) => {
    setForm({ title: p.title, category: p.category || '', excerpt: p.excerpt || '', cover_image_url: p.cover_image_url || '', content: p.content || '', status: p.status })
    setEditId(p.id); setShowForm(true); window.scrollTo({ top: 0 })
  }

  const submit = async (e) => {
    e.preventDefault()
    setError(null)
    setSaving(true)
    try {
      if (editId) await updatePost(editId, form)
      else await createPost(form)
      setShowForm(false); setForm(EMPTY); setEditId(null); load()
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Error al guardar')
    } finally {
      setSaving(false)
    }
  }

  const remove = async (id) => {
    if (!confirm('¿Eliminar este artículo?')) return
    await deletePost(id).catch(() => null)
    load()
  }

  if (loading) return <Spinner />

  return (
    <>
      <Helmet><title>Blog | Listing Admin</title></Helmet>
      <AdminPageHeader
        title="Blog"
        subtitle="Artículos y noticias del portal"
        count={items.length}
        actions={(
          <button className="btn btn-blue" onClick={showForm ? () => setShowForm(false) : startNew}>
            {showForm ? 'Cancelar' : '+ Nuevo artículo'}
          </button>
        )}
      />

      {showForm && (
        <form className="admin-card admin-card-form" onSubmit={submit}>
          <h3 className="admin-card-title">{editId ? 'Editar' : 'Nuevo'} artículo</h3>
          {error && <p className="admin-error">{error}</p>}
          <div className="form-grid">
            <div className="fg full"><label>Título *</label><input required value={form.title} onChange={upd('title')} /></div>
            <div className="fg"><label>Categoría</label><input value={form.category} onChange={upd('category')} /></div>
            <div className="fg"><label>Estado</label>
              <select value={form.status} onChange={upd('status')}>
                <option value="draft">Borrador</option>
                <option value="published">Publicado</option>
              </select>
            </div>
            <div className="fg full"><label>Imagen de portada (URL)</label><input value={form.cover_image_url} onChange={upd('cover_image_url')} /></div>
            <div className="fg full"><label>Resumen</label><textarea rows={2} value={form.excerpt} onChange={upd('excerpt')} /></div>
            <div className="fg full"><label>Contenido</label><textarea rows={8} value={form.content} onChange={upd('content')} /></div>
          </div>
          <button className="btn btn-blue" disabled={saving} style={{ marginTop: 14 }}>
            {saving ? 'Guardando…' : editId ? 'Guardar cambios' : 'Crear artículo'}
          </button>
        </form>
      )}

      {items.length === 0 ? (
        <div className="adm-empty">
          <span className="ico"><IconFile size={26} /></span>
          <b>Sin artículos</b>
          No hay artículos publicados todavía.
        </div>
      ) : (
        <div className="adm-table">
          {items.map((p) => (
            <div className="adm-row" key={p.id}>
              <div className="grow">
                <div className="name">{p.title}</div>
                <div className="sub">{p.category || 'Sin categoría'}</div>
              </div>
              <span className={`tag ${p.status === 'published' ? 'green' : 'amber'}`}>
                {p.status === 'published' ? 'Publicado' : 'Borrador'}
              </span>
              <button className="btn btn-outline btn-sm" onClick={() => startEdit(p)}>Editar</button>
              <button className="btn btn-outline btn-sm btn-danger" onClick={() => remove(p.id)}>Eliminar</button>
            </div>
          ))}
        </div>
      )}
    </>
  )
}
