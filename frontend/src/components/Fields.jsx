import { useMemo } from 'react'

export function NumberField({ label, value, setValue, min, max, step = 1 }) {
  return (
    <label className="flex items-center justify-between gap-3 text-sm">
      <span className="whitespace-nowrap text-gray-600 dark:text-gray-300">{label}</span>
      <input
        type="number"
        className="w-28 rounded-md border border-gray-300 bg-white px-2 py-1 text-right text-sm dark:border-gray-700 dark:bg-gray-900"
        value={value}
        min={min}
        max={max}
        step={step}
        onChange={(e) => setValue(Number(e.target.value))}
      />
    </label>
  )
}

export function ColorField({ label, value, setValue }) {
  const hex = useMemo(() => {
    const [r, g, b] = value
    const toHex = (n) => n.toString(16).padStart(2, '0')
    return `#${toHex(r)}${toHex(g)}${toHex(b)}`
  }, [value])

  return (
    <label className="flex items-center justify-between gap-3 text-sm">
      <span className="whitespace-nowrap text-gray-600 dark:text-gray-300">{label}</span>
      <input
        type="color"
        className="h-8 w-14 rounded-md border border-gray-300 bg-white dark:border-gray-700 dark:bg-gray-900"
        value={hex}
        onChange={(e) => {
          const v = e.target.value
          const r = parseInt(v.slice(1, 3), 16)
          const g = parseInt(v.slice(3, 5), 16)
          const b = parseInt(v.slice(5, 7), 16)
          setValue([r, g, b])
        }}
      />
    </label>
  )
}
