import { useEffect, useState } from 'react'
import './index.css'
import { buildAssetUrl, fetchBackgrounds, fetchFonts, generateHandwriting, uploadBackground } from './api/client'
import { ColorField, NumberField } from './components/Fields'
import ToggleTheme from './components/ToggleTheme'

export default function App() {
  const [fonts, setFonts] = useState([])
  const [backgrounds, setBackgrounds] = useState([])
  const [loadingMeta, setLoadingMeta] = useState(true)

  const [text, setText] = useState('2026-05-09更新\n原服务器商家跑路,现暂时使用Azure过渡\n输入要生成的内容，支持换行\n多段文本将自动分页渲染。\n可自行上传背景，建议少量文字逐渐调整参数测试效果，无误后再大批量生成。\n图片不要过大以免长时间等待生成。可以在下方"背景缩放"参数调整背景图片放大倍率。\n有现成字体可选，找一个适合自己的字体。生成后建议再单独生成个人姓名P上保证全局字体一致\n后端不会保留用户图片，每2min执行清理，可放心生成内容\n希望这个项目能帮助到你~!')
  const [font, setFont] = useState('')
  const [fontSize, setFontSize] = useState(85)
  const [lineSpacing, setLineSpacing] = useState(100)
  const [wordSpacing, setWordSpacing] = useState(-10)
  const [fillColor, setFillColor] = useState([0, 0, 0])
  const [leftMargin, setLeftMargin] = useState(100)
  const [topMargin, setTopMargin] = useState(355)
  const [rightMargin, setRightMargin] = useState(90)
  const [bottomMargin, setBottomMargin] = useState(150)
  const [lineSigma, setLineSigma] = useState(2)
  const [wordSigma, setWordSigma] = useState(2)
  const [fontSigma, setFontSigma] = useState(2)
  const [pxSigma, setPxSigma] = useState(1)
  const [pySigma, setPySigma] = useState(1)
  const [thetaSigma, setThetaSigma] = useState(0.08)
  const [background, setBackground] = useState('')
  const [backgroundScale, setBackgroundScale] = useState(2.0)
  const [outputFormat, setOutputFormat] = useState('webp')

  const [uploading, setUploading] = useState(false)
  const [genLoading, setGenLoading] = useState(false)
  const [outputs, setOutputs] = useState([])
  const [error, setError] = useState('')
  const [formError, setFormError] = useState('')

  useEffect(() => {
    let cancelled = false

    async function loadMeta() {
      setLoadingMeta(true)
      try {
        const [fontItems, backgroundItems] = await Promise.all([fetchFonts(), fetchBackgrounds()])
        if (cancelled) return
        setFonts(fontItems)
        setBackgrounds(backgroundItems)
        setFont((prev) => prev || fontItems[0]?.file || '')
        setBackground((prev) => prev || backgroundItems[0]?.file || '')
      } catch (requestError) {
        if (!cancelled) {
          setError(requestError instanceof Error ? requestError.message : '请求失败，请稍后重试')
        }
      } finally {
        if (!cancelled) setLoadingMeta(false)
      }
    }

    void loadMeta()
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    const trimmed = text.trim()
    if (!trimmed) {
      setFormError('请在“内容”中填写内容')
      return
    }
    if (fontSize > lineSpacing) {
      setFormError('字体大小需小于或等于行间距')
      return
    }
    setFormError('')
  }, [text, fontSize, lineSpacing])

  const onUploadBackground = async (file) => {
    if (!file) return
    setUploading(true)
    setError('')
    try {
      const uploaded = await uploadBackground(file)
      const uploadedFile = uploaded?.path?.split('/').pop() || ''
      if (!uploadedFile) {
        throw new Error('上传成功但返回结果不完整')
      }
      const item = { name: file.name, file: uploadedFile, url: uploaded.path }
      setBackgrounds((prev) => [item, ...prev.filter((bg) => bg.file !== item.file)])
      setBackground(uploadedFile)
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : '请求失败，请稍后重试')
    } finally {
      setUploading(false)
    }
  }

  const onGenerate = async () => {
    const trimmed = text.trim()
    if (!trimmed || formError) {
      const message = formError || '请在“内容”中填写内容'
      setError(message)
      return
    }

    setGenLoading(true)
    setOutputs([])
    setError('')

    const payload = {
      text,
      font: font || undefined,
      font_size: fontSize,
      line_spacing: lineSpacing,
      word_spacing: wordSpacing,
      fill_color: fillColor,
      left_margin: leftMargin,
      top_margin: topMargin,
      right_margin: rightMargin,
      bottom_margin: bottomMargin,
      line_spacing_sigma: lineSigma,
      word_spacing_sigma: wordSigma,
      font_size_sigma: fontSigma,
      perturb_x_sigma: pxSigma,
      perturb_y_sigma: pySigma,
      perturb_theta_sigma: thetaSigma,
      background: background || undefined,
      background_scale: backgroundScale,
      output_format: outputFormat,
    }

    try {
      const generated = await generateHandwriting(payload)
      setOutputs(generated)
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : '请求失败，请稍后重试')
    } finally {
      setGenLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-7xl p-4 md:p-6">
      <header className="mb-6 flex items-center justify-between">
        <h1 className="text-xl font-semibold">手写体生成器</h1>
        <div className="flex items-center gap-3">
          <ToggleTheme />
        </div>
      </header>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        <section className="md:col-span-1 rounded-lg border border-gray-200 p-4 dark:border-gray-800">
          <h2 className="mb-3 text-base font-medium">参数设置</h2>
          <div className="mb-4">
            <label className="mb-1 block text-sm text-gray-600 dark:text-gray-300">内容</label>
            <textarea
              className="h-40 w-full resize-y rounded-md border border-gray-300 bg-white p-2 text-sm leading-relaxed dark:border-gray-700 dark:bg-gray-900"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="请输入要生成的文字，支持换行"
            />
          </div>

          <div className="mb-4">
            <label className="mb-1 block text-sm text-gray-600 dark:text-gray-300">字体</label>
            <select
              className="w-full rounded-md border border-gray-300 bg-white p-2 text-sm dark:border-gray-700 dark:bg-gray-900"
              value={font}
              onChange={(e) => setFont(e.target.value)}
              disabled={loadingMeta}
            >
              {fonts.map((f) => (
                <option key={f.file} value={f.file}>{f.name}</option>
              ))}
            </select>
          </div>

          <div className="mb-4">
            <label className="mb-1 block text-sm text-gray-600 dark:text-gray-300">背景</label>
            <div className="flex items-center gap-2">
              <select
                className="w-full rounded-md border border-gray-300 bg-white p-2 text-sm dark:border-gray-700 dark:bg-gray-900"
                value={background}
                onChange={(e) => setBackground(e.target.value)}
                disabled={loadingMeta}
              >
                {backgrounds.map((bg) => (
                  <option key={`${bg.file}-${bg.url}`} value={bg.file}>{bg.name}</option>
                ))}
              </select>
              <label className="cursor-pointer rounded-md border border-dashed px-3 py-2 text-sm hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-800">
                上传
                <input type="file" accept="image/png,image/jpeg,image/webp" className="hidden" onChange={(e) => void onUploadBackground(e.target.files?.[0])} />
              </label>
            </div>
            {uploading && <p className="mt-1 text-xs text-gray-500">正在上传...</p>}
          </div>

          <div className="mb-2 grid grid-cols-2 gap-3">
            <NumberField label="字体大小" value={fontSize} setValue={setFontSize} min={8} max={200} />
            <NumberField label="行间距" value={lineSpacing} setValue={setLineSpacing} min={16} max={400} />
            <NumberField label="字间距" value={wordSpacing} setValue={setWordSpacing} min={-100} max={100} step={0.5} />
            <ColorField label="颜色" value={fillColor} setValue={setFillColor} />
            <NumberField label="左边距" value={leftMargin} setValue={setLeftMargin} min={0} max={1000} />
            <NumberField label="上边距" value={topMargin} setValue={setTopMargin} min={0} max={1000} />
            <NumberField label="右边距" value={rightMargin} setValue={setRightMargin} min={0} max={1000} />
            <NumberField label="下边距" value={bottomMargin} setValue={setBottomMargin} min={0} max={1000} />
            <NumberField label="行距扰动" value={lineSigma} setValue={setLineSigma} min={0} max={20} step={0.1} />
            <NumberField label="字距扰动" value={wordSigma} setValue={setWordSigma} min={0} max={20} step={0.1} />
            <NumberField label="字号扰动" value={fontSigma} setValue={setFontSigma} min={0} max={20} step={0.1} />
            <NumberField label="横向扰动" value={pxSigma} setValue={setPxSigma} min={0} max={20} step={0.1} />
            <NumberField label="纵向扰动" value={pySigma} setValue={setPySigma} min={0} max={20} step={0.1} />
            <NumberField label="旋转扰动" value={thetaSigma} setValue={setThetaSigma} min={0} max={1} step={0.01} />
            <NumberField label="背景缩放" value={backgroundScale} setValue={setBackgroundScale} min={0.1} max={10} step={0.1} />
          </div>
          {formError && <p className="mb-4 text-xs text-red-600 dark:text-red-400">{formError}</p>}

          <div className="mb-4">
            <label className="mb-1 block text-sm text-gray-600 dark:text-gray-300">输出格式</label>
            <select className="w-full rounded-md border border-gray-300 bg-white p-2 text-sm dark:border-gray-700 dark:bg-gray-900" value={outputFormat} onChange={(e) => setOutputFormat(e.target.value)}>
              <option value="webp">webp</option>
              <option value="png">png</option>
            </select>
          </div>

          <button onClick={() => void onGenerate()} disabled={genLoading || Boolean(formError)} className="inline-flex w-full items-center justify-center rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-60">
            {genLoading ? '生成中...' : '生成'}
          </button>

          {error && <p className="mt-3 text-sm text-red-600 dark:text-red-400">{error}</p>}
        </section>

        <section className="md:col-span-2">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-base font-medium">预览</h2>
            <span className="text-xs text-gray-500">共 {outputs.length} 张</span>
          </div>
          {outputs.length === 0 && (
            <div className="flex h-64 items-center justify-center rounded-lg border border-dashed border-gray-300 text-sm text-gray-500 dark:border-gray-700">
              {genLoading ? '生成中，请稍候...' : '尚未生成，点击左侧“生成”按钮'}
            </div>
          )}
          <h3 className="mb-4 text-sm text-gray-500 dark:text-gray-400">联系方式: acgn345@outlook.com</h3>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {outputs.map((url, idx) => (
              <div key={`${url}-${idx}`} className="overflow-hidden rounded-lg border border-gray-200 dark:border-gray-800">
                <img src={buildAssetUrl(url)} alt={`output-${idx}`} className="block w-full" />
                <div className="flex items-center justify-between px-3 py-2 text-xs text-gray-600 dark:text-gray-300">
                  <span className="truncate">{url}</span>
                  <a className="text-blue-600 hover:underline dark:text-blue-400" href={buildAssetUrl(url)} target="_blank" rel="noreferrer">新窗口打开</a>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}
