import { useEffect, useMemo, useState } from 'react';
import { useGenieChat } from '@databricks/appkit-ui/react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  Badge,
  Alert,
  AlertDescription,
  Button,
} from '@databricks/appkit-ui/react';

interface WhoAmI { email?: string | null; user?: string | null }

export function GeniePage() {
  // Trust element #1 — authenticated identity
  const [me, setMe] = useState<WhoAmI | null>(null);
  useEffect(() => {
    fetch('/api/whoami').then((r) => (r.ok ? r.json() : null)).then(setMe).catch(() => {});
  }, []);

  const { messages, status, sendMessage, reset, error } = useGenieChat({ alias: 'default' });
  const [input, setInput] = useState('');

  // Trust element #2 — surface the generated SQL from the latest attachment
  const lastSql = useMemo(() => {
    for (const m of [...messages].reverse()) {
      for (const a of m.attachments ?? []) {
        if (a.query?.query) return a.query;
      }
    }
    return null;
  }, [messages]);

  function ask() {
    const q = input.trim();
    if (!q) return;
    sendMessage(q);
    setInput('');
  }

  return (
    <div className="space-y-4 w-full max-w-4xl mx-auto">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-foreground">Ask the Workbench</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Natural-language questions over the root-cause serving layer (rc_* tables).
          </p>
        </div>
        {/* #1 identity chip */}
        <Badge variant="secondary">{me?.email ?? 'Signed in'}</Badge>
      </div>

      {/* #5 governance / execution-identity note — OBO is wired via user_api_scopes: [dashboards.genie] */}
      <Alert>
        <AlertDescription className="text-xs">
          Queries run <strong>on your behalf</strong> (OBO) — results respect your own Unity Catalog permissions.
          Answers are AI-generated; verify against the generated SQL below.
        </AlertDescription>
      </Alert>

      <div className="flex gap-2">
        <input
          className="flex-1 border rounded-md px-3 py-2 text-sm bg-background"
          placeholder="e.g. Which A-class SKUs are unrecoverable and chronic?"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') ask(); }}
        />
        <Button onClick={ask} disabled={status === 'streaming'}>Ask</Button>
        <Button variant="ghost" onClick={reset}>New</Button>
      </div>

      {/* #3 streaming / status — never a frozen spinner */}
      {status === 'streaming' && <p className="text-sm text-muted-foreground">Analyzing your data…</p>}
      {status === 'error' && (
        <Alert variant="destructive"><AlertDescription>{error ?? 'Genie failed — rephrase or retry.'}</AlertDescription></Alert>
      )}

      {/* conversation transcript */}
      <div className="space-y-3">
        {messages.length === 0 && status === 'idle' && (
          <div className="text-sm text-muted-foreground py-8 text-center">
            Ask a question to start. Try: “Top 10 A-class shortages by dollars at risk.”
          </div>
        )}
        {messages.map((m) => (
          <div key={m.id} className={m.role === 'user' ? 'text-right' : ''}>
            <div className={`inline-block rounded-lg px-3 py-2 text-sm ${m.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted'}`}>
              {m.content}
            </div>
          </div>
        ))}
      </div>

      {/* #2 generated SQL card */}
      {lastSql && (
        <Card className="shadow-sm">
          <CardHeader>
            <CardTitle className="text-sm">Generated SQL</CardTitle>
            <CardDescription>{lastSql.title ?? lastSql.description ?? 'How this answer was computed'}</CardDescription>
          </CardHeader>
          <CardContent>
            <pre className="overflow-auto text-xs bg-muted rounded p-3">{lastSql.query}</pre>
          </CardContent>
        </Card>
      )}

      {/* #4 per-answer disclaimer */}
      <p className="text-xs text-muted-foreground">
        AI-generated from your data via Genie — review the generated SQL before trusting results.
      </p>
    </div>
  );
}
