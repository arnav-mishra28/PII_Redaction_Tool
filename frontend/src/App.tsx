import { useState } from 'react';
import { Document, Packer, Paragraph } from 'docx';
import { jsPDF } from 'jspdf';
import { Clipboard, Download, FileUp, ShieldCheck, Sparkles, ScanSearch, Eraser } from 'lucide-react';

type Entity = { entity_type: string; start: number; end: number; confidence: number; risk_level: string };
const API = import.meta.env.VITE_API_URL ?? `${window.location.protocol}//${window.location.hostname}:8000`;
const example = 'Hi support, please update the account for Maya Iyer. Email: maya.iyer@example.test, phone: +91 98765 43210. PAN: ABCDE1234F. DOB: 12/08/1994.';

function App() {
  const [text, setText] = useState('');
  const [entities, setEntities] = useState<Entity[]>([]);
  const [redacted, setRedacted] = useState('');
  const [mode, setMode] = useState('typed');
  const [busy, setBusy] = useState(false);
  const [fileName, setFileName] = useState('');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [error, setError] = useState('');

  const request = async (path: string, options: RequestInit) => {
    const response = await fetch(`${API}${path}`, options);
    const result = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(result.detail || `Request failed (${response.status})`);
    return result;
  };

  const run = async (action: 'detect' | 'redact') => {
    if (!text.trim()) { setError('Add some text first, or try the example.'); return; }
    setBusy(true); setError('');
    try {
      const data = await request(`/api/v1/${action}/text`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text, masking_mode: mode }) });
      setEntities(data.entities ?? []);
      if (action === 'redact') setRedacted(data.redacted_text ?? '');
    } catch (requestError) { setError(requestError instanceof Error ? requestError.message : 'Could not reach the redaction service.'); }
    finally { setBusy(false); }
  };

  const upload = async (file: File) => {
    setFileName(file.name); setUploadedFile(file); setBusy(true); setError('');
    try {
      const data = new FormData(); data.append('file', file);
      const result = await request('/api/v1/detect/document', { method: 'POST', body: data });
      if (!result.extracted_text) throw new Error('No readable text was found. Scanned PDFs may need OCR.');
      setText(result.extracted_text); setRedacted(''); setEntities(result.entities ?? []);
    } catch (requestError) { setError(requestError instanceof Error ? requestError.message : 'Could not process this document. Check that the API is running on port 8000.'); }
    finally { setBusy(false); }
  };

  const shownText = redacted || text;
  const saveFile = (blob: Blob, name: string) => { const link = document.createElement('a'); link.href = URL.createObjectURL(blob); link.download = name; link.click(); URL.revokeObjectURL(link.href); };
  const copyText = async () => { if (!shownText) { setError('There is no extracted text to copy yet.'); return; } try { await navigator.clipboard.writeText(shownText); setError('Text copied to your clipboard.'); } catch { setError('Clipboard access was blocked. Select the preview text and copy it manually.'); } };
  const downloadPdf = () => { if (uploadedFile && fileName.toLowerCase().endsWith('.pdf')) { void downloadOriginalFormat(); return; } if (!shownText) { setError('There is no text to download yet.'); return; } const pdf = new jsPDF(); pdf.setFont('courier', 'normal'); pdf.setFontSize(10); pdf.text(pdf.splitTextToSize(shownText, 180), 15, 18); saveFile(pdf.output('blob'), `${redacted ? 'redacted-' : 'extracted-'}${fileName.replace(/\.[^.]+$/, '') || 'document'}.pdf`); };
  const downloadDocx = async () => { if (uploadedFile && fileName.toLowerCase().endsWith('.docx')) { await downloadOriginalFormat(); return; } if (!shownText) { setError('There is no text to download yet.'); return; } const document = new Document({ sections: [{ children: shownText.split('\n').map(line => new Paragraph(line)) }] }); saveFile(await Packer.toBlob(document), `${redacted ? 'redacted-' : 'extracted-'}${fileName.replace(/\.[^.]+$/, '') || 'document'}.docx`); };
  const downloadOriginalFormat = async () => {
    if (!uploadedFile) return;
    setBusy(true); setError('');
    try {
      const data = new FormData(); data.append('file', uploadedFile);
      const response = await fetch(`${API}/api/v1/redact/document/file?masking_mode=${mode}`, { method: 'POST', body: data });
      if (!response.ok) { const result = await response.json().catch(() => ({})); throw new Error(result.detail || `Could not create the redacted ${uploadedFile.name}`); }
      saveFile(await response.blob(), `redacted-${uploadedFile.name}`);
    } catch (requestError) { setError(requestError instanceof Error ? requestError.message : 'Could not download the redacted document.'); }
    finally { setBusy(false); }
  };

  const highlighted = entities.length ? entities.reduce((parts, entity, index) => {
    const previous = index ? entities[index - 1].end : 0;
    return [...parts, <span key={`t-${index}`}>{text.slice(previous, entity.start)}</span>, <mark key={`m-${index}`} className={`risk-${entity.risk_level}`} title={`${entity.entity_type} - ${Math.round(entity.confidence * 100)}%`}>{text.slice(entity.start, entity.end)}</mark>];
  }, [] as React.ReactNode[]).concat(text.slice(entities[entities.length - 1].end)) : [text];

  return <main><header><div className="brand"><span className="brand-mark"><ShieldCheck size={20} /></span><span>VEIL</span></div><span className="status"><i /> Local-first protection</span></header><section className="intro"><p className="eyebrow">PII intelligence / 01</p><h1>Make sensitive text<br /><em>unrecognizable.</em></h1><p className="lede">A hybrid detector for support teams. Find context, mask risk, and move information forward without exposing the people inside it.</p></section><section className="workspace"><div className="toolbar"><div className="tab active"><ScanSearch size={16} /> Workspace</div><label className="upload"><FileUp size={16} /> {busy ? 'Processing...' : fileName || 'Upload document'}<input type="file" accept=".pdf,.docx,.txt,.json,.csv" onChange={event => event.target.files?.[0] && upload(event.target.files[0])} /></label></div><div className="panels"><div className="panel input-panel"><div className="panel-head"><span>Source text</span><button onClick={() => { setText(example); setError(''); }}><Sparkles size={14} /> Try example</button></div><textarea value={text} onChange={event => setText(event.target.value)} placeholder="Paste a ticket, transcript, or note here..." /><div className="panel-foot"><span>{text.length.toLocaleString()} characters</span><button className="clear" onClick={() => { setText(''); setEntities([]); setRedacted(''); setUploadedFile(null); setFileName(''); setError(''); }}>Clear</button></div></div><div className="panel output-panel"><div className="panel-head"><span>Protected preview</span><div className="export-actions"><button onClick={copyText} disabled={!shownText}><Clipboard size={14} /> Copy</button><button onClick={downloadPdf} disabled={!shownText}><Download size={14} /> PDF</button><button onClick={downloadDocx} disabled={!shownText}><Download size={14} /> DOCX</button>{uploadedFile && <button onClick={downloadOriginalFormat} disabled={!redacted || busy}><Download size={14} /> Original format</button>}</div></div><div className="preview">{redacted ? redacted : highlighted}</div><div className="panel-foot"><span>{entities.length} entities found</span><span className="legend"><i className="dot high" /> High risk <i className="dot medium" /> Medium</span></div></div></div>{error && <p className="error" role="alert">{error}</p>}<div className="actions"><div className="mode"><span>Masking</span>{['typed', 'black', 'partial'].map(value => <button key={value} className={mode === value ? 'selected' : ''} onClick={() => setMode(value)}>{value}</button>)}</div><div className="action-buttons"><button className="secondary" onClick={() => run('detect')} disabled={busy}><ScanSearch size={17} /> Detect PII</button><button className="primary" onClick={() => run('redact')} disabled={busy}><Eraser size={17} /> {busy ? 'Processing...' : 'Redact text'}</button></div></div></section><section className="insights"><div><span className="metric">{entities.length}</span><span>detected entities</span></div><div><span className="metric">{entities.filter(entity => entity.risk_level === 'high' || entity.risk_level === 'critical').length}</span><span>high attention</span></div><p>Regex precision for structured identifiers.<br />spaCy context for names and places.</p></section></main>;
}
export default App;
