import React, { useState, useEffect } from 'react';
import { Card, Badge, Button } from '../components/common';
import { copilotService } from '../services';

export const AICopilotPage: React.FC = () => {
  const [prompts, setPrompts] = useState<any[]>([]);
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<Array<{ role: 'user' | 'assistant'; text: string; data?: any }>>([
    {
      role: 'assistant',
      text: 'Welcome to the ReliefChain AI Emergency Operations Copilot. I analyze live telemetry, multi-hazard perimeters, SPHERE supply buffers, and responder availability to provide verified response directives.',
    },
  ]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadPrompts();
  }, []);

  const loadPrompts = async () => {
    try {
      const res = await copilotService.getSuggestedPrompts();
      if (res?.prompts) setPrompts(res.prompts);
    } catch (e) {
      console.warn(e);
    }
  };

  const handleSend = async (textToSend?: string) => {
    const q = textToSend || query;
    if (!q.trim()) return;

    const newMsgs = [...messages, { role: 'user' as const, text: q }];
    setMessages(newMsgs);
    setQuery('');
    setLoading(true);

    try {
      const res = await copilotService.query(q);
      setMessages([...newMsgs, { role: 'assistant', text: res.answer_markdown, data: res }]);
    } catch (err: any) {
      setMessages([...newMsgs, { role: 'assistant', text: `Error: ${err.message}` }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-black text-slate-100 flex items-center gap-2">
            <span>🤖</span> AI Disaster Copilot
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Rule-based operational assistant for incident reasoning, shortage diagnosis, and smart dispatch.
          </p>
        </div>
        <Badge variant="success">● REAL-TIME DECISION SUPPORT</Badge>
      </div>

      {/* Suggested Prompt Chips */}
      <Card>
        <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">⚡ Quick Command Prompts:</div>
        <div className="flex flex-wrap gap-2">
          {prompts.map((p) => (
            <Button
              key={p.id}
              variant="outline"
              size="sm"
              onClick={() => handleSend(p.prompt)}
              className="text-xs"
            >
              {p.category === 'critical_incidents' ? '🚨' : p.category === 'resource_shortages' ? '📦' : '🦺'} {p.title}
            </Button>
          ))}
        </div>
      </Card>

      {/* Chat Stream Console */}
      <Card className="min-h-[460px] flex flex-col justify-between">
        <div className="space-y-4 max-h-[380px] overflow-y-auto pr-2">
          {messages.map((m, idx) => (
            <div
              key={idx}
              className={`p-4 rounded-xl text-xs leading-relaxed max-w-[88%] ${
                m.role === 'user'
                  ? 'ml-auto bg-cyan-500 text-slate-950 font-bold'
                  : 'bg-slate-950/80 border border-slate-800 text-slate-200'
              }`}
            >
              {m.role === 'assistant' && (
                <div className="flex justify-between items-center mb-2 pb-1 border-b border-slate-800 text-cyan-400 font-bold">
                  <span>ReliefChain AI Copilot</span>
                  <Badge variant="primary" className="text-[10px]">VERIFIED CITATIONS</Badge>
                </div>
              )}
              <div className="whitespace-pre-line">{m.text}</div>
              {m.data?.actionable_recommendations && (
                <div className="mt-3 pt-2 border-t border-slate-800/80 text-cyan-300">
                  <div className="font-bold text-[11px] uppercase tracking-wider mb-1">Action Directives:</div>
                  <ul className="list-disc list-inside space-y-1">
                    {m.data.actionable_recommendations.map((a: string, i: number) => (
                      <li key={i}>{a}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
          {loading && (
            <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl text-xs text-slate-400 animate-pulse">
              🤖 <em>Analyzing live multi-hazard perimeters & SPHERE supply chain telemetry...</em>
            </div>
          )}
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex gap-2 mt-4 pt-4 border-t border-slate-800"
        >
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask Copilot (e.g. 'Show critical incidents' or 'Find food shortages')..."
            className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-4 py-2.5 text-xs text-slate-100 focus:outline-none focus:border-cyan-400"
          />
          <Button variant="primary" size="md">Send Query</Button>
        </form>
      </Card>
    </div>
  );
};
