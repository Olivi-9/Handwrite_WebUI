import { useState } from 'react'

export default function ToggleTheme() {
  const [dark, setDark] = useState(() => document.documentElement.classList.contains('dark'))

  const toggle = () => {
    const next = !dark
    setDark(next)
    document.documentElement.classList.toggle('dark', next)
    try {
      localStorage.setItem('theme', next ? 'dark' : 'light')
    } catch (error) {
      void error
    }
  }

  return (
    <button onClick={toggle} className="inline-flex items-center gap-2 rounded-md border px-3 py-1.5 text-sm hover:bg-gray-50 dark:hover:bg-gray-800">
      <span>{dark ? '🌙' : '🌞'}</span>
      <span>{dark ? '深色' : '浅色'}</span>
    </button>
  )
}
