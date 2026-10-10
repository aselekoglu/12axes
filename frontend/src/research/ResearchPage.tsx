import { useEffect, useMemo, useState } from 'react';
import { LANG } from '../i18n';
import type { AnswerValue } from '../types/quiz';
import './research.css';

type Question = { id: string; axis_id: string; text: string };
type Archetype = { id: string; text: string; options: { id: string; text: string }[] };
type ResearchForm = {
  instrument_version: string;
  form_index: number;
  questions: Question[];
  archetype_questions: Archetype[];
  notice: string;
};
type SessionResponse = { participant_token: string; form: ResearchForm };

const BASE = (import.meta.env.VITE_RESEARCH_API_URL ?? '').replace(/\/$/, '');
const ENABLE_FIELDING = import.meta.env.VITE_RESEARCH_ENABLE_ENROLLMENT === 'true';
const CONSENT_VERSION = import.meta.env.VITE_RESEARCH_CONSENT_VERSION ?? '';
const LABELS: Record<AnswerValue, { en: string; pt: string }> = {
  STRONGLY_DISAGREE: { en: 'Strongly disagree', pt: 'Discordo totalmente' },
  DISAGREE: { en: 'Disagree', pt: 'Discordo' },
  NEUTRAL: { en: 'Neither', pt: 'Neutro' },
  AGREE: { en: 'Agree', pt: 'Concordo' },
  STRONGLY_AGREE: { en: 'Strongly agree', pt: 'Concordo totalmente' },
};
const VALUES = Object.keys(LABELS) as AnswerValue[];

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(BASE + '/research-api' + path, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
    cache: 'no-store',
  });
  if (!response.ok) {
    throw new Error('Research API returned HTTP ' + response.status);
  }
  return response.status === 204 ? (undefined as T) : (response.json() as Promise<T>);
}

export default function ResearchPage() {
  const lang = LANG === 'pt' ? 'pt' : 'en';
  const pt = lang === 'pt';
  const [form, setForm] = useState<ResearchForm | null>(null);
  const [answers, setAnswers] = useState<Record<string, AnswerValue>>({});
  const [archetype, setArchetype] = useState<Record<string, string>>({});
  const [current, setCurrent] = useState(0);
  const [token, setToken] = useState<string | null>(null);
  const [consent, setConsent] = useState(false);
  const [adult, setAdult] = useState(false);
  const [invite, setInvite] = useState('');
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [withdrawn, setWithdrawn] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    api<ResearchForm>('/preview?form_index=0&lang=' + lang, { signal: controller.signal })
      .then(setForm)
      .catch((e: Error) => { if (e.name !== 'AbortError') setError(e.message); })
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, [lang]);

  const count = form ? form.questions.length + form.archetype_questions.length : 0;
  const indexQuestion = form && current < form.questions.length ? form.questions[current] : null;
  const indexArchetype = form && current >= form.questions.length
    ? form.archetype_questions[current - form.questions.length] : null;
  const allDone = !!form && form.questions.every(q => answers[q.id]) &&
    form.archetype_questions.every(q => archetype[q.id]);
  const currentAnswered = indexQuestion ? !!answers[indexQuestion.id]
    : indexArchetype ? !!archetype[indexArchetype.id] : false;
  const completion = useMemo(() => form
    ? form.questions.filter(q => answers[q.id]).length +
      form.archetype_questions.filter(q => archetype[q.id]).length : 0,
  [form, answers, archetype]);

  async function enroll() {
    if (!consent || !adult || !invite || !CONSENT_VERSION) {
      setError(pt ? 'Consentimento, elegibilidade e convite obrigatórios.' :
        'Consent, adult eligibility and study invitation are required.');
      return;
    }
    setBusy(true); setError(null);
    try {
      const session = await api<SessionResponse>('/sessions?lang=' + lang, {
        method: 'POST',
        body: JSON.stringify({
          consent: true, age_18_plus: true, invite_code: invite,
          consent_version: CONSENT_VERSION,
        }),
      });
      setForm(session.form); setToken(session.participant_token);
      setAnswers({}); setArchetype({}); setCurrent(0);
      setInvite(''); // do not persist invitation credential
    } catch (e) { setError((e as Error).message); }
    finally { setBusy(false); }
  }

  async function submit() {
    if (!form || !allDone) return;
    if (!token) { setSubmitted(true); return; } // local preview; never uploads answers
    setBusy(true); setError(null);
    try {
      await api<void>('/responses', {
        method: 'POST',
        headers: { Authorization: 'Bearer ' + token },
        body: JSON.stringify({ answers, archetype }),
      });
      setSubmitted(true); setAnswers({}); setArchetype({});
    } catch (e) { setError((e as Error).message); }
    finally { setBusy(false); }
  }

  async function withdraw() {
    if (!token) return;
    setBusy(true); setError(null);
    try {
      await api<void>('/withdraw', { method: 'POST',
        headers: { Authorization: 'Bearer ' + token } });
      setWithdrawn(true); setToken(null); setAnswers({}); setArchetype({});
    } catch (e) { setError((e as Error).message); }
    finally { setBusy(false); }
  }

  return <main className="research-shell">
    <a className="research-back" href="/">← 12Axes</a>
    <p className="research-eyebrow">12AXES / MEASUREMENT RESEARCH</p>
    <h1>{pt ? 'Pesquisa de validação' : 'Measurement research'}</h1>
    <p className="research-lead">{pt
      ? 'Avaliamos se as perguntas realmente medem dimensões políticas distintas. Este projeto ainda não é uma escala cientificamente validada.'
      : 'We are testing whether the questions genuinely measure distinct political dimensions. The project is not yet a scientifically validated scale.'}</p>
    {!token && <div className="research-warning" role="note">
      {pt ? 'Prévia de desenvolvimento: nenhuma resposta é transmitida ou armazenada.' :
        'Development preview: no political answers are transmitted or stored.'}
    </div>}
    {loading && <p role="status">{pt ? 'Carregando…' : 'Loading…'}</p>}
    {error && <p className="research-error" role="alert">{error}</p>}
    {!loading && !form && <p>{pt ? 'Inicie a API de pesquisa local na porta 8090.' :
      'Start the local research API on port 8090. The public quiz API is separate.'}</p>}
    {form && <>
      <p className="research-caption">Instrument {form.instrument_version} · {count} {pt ? 'itens' : 'items'}</p>
      {ENABLE_FIELDING && !token && !submitted && <section className="research-panel">
        <h2>{pt ? 'Participação voluntária' : 'Voluntary participation'}</h2>
        <p>{pt ? 'As respostas tratam de opiniões políticas sensíveis. A participação é opcional. Você pode retirar seus dados usando o token da sessão. Somente participe se recebeu o documento formal de consentimento da equipe de pesquisa.' :
          'Responses contain sensitive political opinions. Participation is optional. You may withdraw with your session token. Only participate after receiving and reading the formal consent document from the research team.'}</p>
        <label><input type="checkbox" checked={adult} onChange={e => setAdult(e.target.checked)}/> {pt ? 'Tenho pelo menos 18 anos.' : 'I am at least 18 years old.'}</label>
        <label><input type="checkbox" checked={consent} onChange={e => setConsent(e.target.checked)}/> {pt ? 'Li o consentimento formal e concordo.' : 'I read the formal consent document and agree.'}</label>
        <label>{pt ? 'Código de convite' : 'Study invitation code'}
          <input type="password" value={invite} onChange={e => setInvite(e.target.value)} autoComplete="off"/>
        </label>
        <button type="button" className="research-primary" disabled={busy || !adult || !consent || !invite} onClick={enroll}>
          {pt ? 'Iniciar sessão consentida' : 'Start consented session'}
        </button>
        <p className="research-caption">{pt ? 'O modo de campo exige aprovação externa e está desativado por padrão.' :
          'Real collection requires external authorization and is disabled by default.'}</p>
      </section>}
      {!submitted && !withdrawn && <section className="research-panel" aria-labelledby="research-question">
        <div className="research-progress-top"><span>{current + 1} / {count}</span>
          <span>{completion} {pt ? 'respondidos' : 'answered'}</span></div>
        <progress value={completion} max={count}/>
        {indexQuestion && <>
          <span className="research-axis">{indexQuestion.axis_id}</span>
          <h2 id="research-question">{indexQuestion.text}</h2>
          <div className="research-options" role="radiogroup" aria-label="Agreement">
            {VALUES.map(value => <button key={value} type="button" role="radio"
              aria-checked={answers[indexQuestion.id] === value}
              className={answers[indexQuestion.id] === value ? 'research-option selected' : 'research-option'}
              onClick={() => setAnswers(prev => ({...prev, [indexQuestion.id]:value}))}>
              {LABELS[value][lang]}</button>)}
          </div>
        </>}
        {indexArchetype && <>
          <span className="research-axis">{pt ? 'Questão de arquétipo' : 'Archetype question'}</span>
          <h2 id="research-question">{indexArchetype.text}</h2>
          <div className="research-options" role="radiogroup" aria-label="Archetype">
            {indexArchetype.options.map(opt => <button key={opt.id} role="radio" type="button"
              aria-checked={archetype[indexArchetype.id] === opt.id}
              className={archetype[indexArchetype.id] === opt.id ? 'research-option selected' : 'research-option'}
              onClick={() => setArchetype(prev => ({...prev, [indexArchetype.id]:opt.id}))}>
              {opt.text}</button>)}
          </div>
        </>}
        <div className="research-nav">
          <button type="button" disabled={current === 0} onClick={() => setCurrent(i=>Math.max(0,i-1))}>
            {pt ? 'Anterior' : 'Back'}</button>
          {current < count-1
            ? <button type="button" className="research-primary" disabled={!currentAnswered}
                onClick={() => setCurrent(i=>Math.min(count-1,i+1))}>
                {pt ? 'Próxima' : 'Next'}</button>
            : <button type="button" className="research-primary" disabled={busy || !allDone} onClick={submit}>
                {token ? (pt ? 'Enviar respostas' : 'Submit responses') :
                  (pt ? 'Concluir prévia (sem salvar)' : 'Finish preview (no saving)')}</button>}
        </div>
      </section>}
      {submitted && <section className="research-panel" role="status">
        <h2>{token ? (pt ? 'Respostas enviadas' : 'Responses submitted') :
          (pt ? 'Prévia concluída' : 'Preview complete')}</h2>
        <p>{token ? (pt ? 'Guarde o token para retirar sua participação.' :
          'Keep your access token if you wish to withdraw.') :
          (pt ? 'Suas respostas não foram salvas.' : 'Your answers were not saved.')}</p>
      </section>}
      {withdrawn && <div className="research-panel" role="status">
        {pt ? 'Seu registro foi retirado do banco ativo.' : 'Your record was deleted from the active database.'}
      </div>}
      {token && !withdrawn && <section className="research-panel">
        <h2>{pt ? 'Retirar participação' : 'Withdraw participation'}</h2>
        <p>{pt ? 'O token permanece somente na memória desta aba. Depois de atualizar a página, você precisará guardar o token para solicitar retirada.' :
          'The access token exists only in this tab memory. After refreshing, you must have saved it to request withdrawal.'}</p>
        <details><summary>{pt ? 'Mostrar token de retirada' : 'Show withdrawal token'}</summary>
          <code className="research-token">{token}</code></details>
        <button type="button" disabled={busy} onClick={withdraw}>
          {pt ? 'Excluir minha participação' : 'Delete my participation'}</button>
      </section>}
    </>}
  </main>;
}
