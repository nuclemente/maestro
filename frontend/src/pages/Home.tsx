import { useState } from 'react';
import toast from 'react-hot-toast';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import Modal from '../components/ui/Modal';
import { api } from '../lib/api';

interface HealthPayload {
  status: string;
  service: string;
  env: string;
  timestamp: string;
}

export default function Home() {
  const [modalOpen, setModalOpen] = useState(false);
  const [health, setHealth] = useState<HealthPayload | null>(null);
  const [loading, setLoading] = useState(false);

  async function pingBackend() {
    setLoading(true);
    try {
      const data = await api.get<HealthPayload>('/health');
      setHealth(data);
      toast.success('Backend respondeu OK');
    } catch (err) {
      toast.error(`Falha ao consultar backend: ${(err as Error).message}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="mx-auto max-w-3xl px-4 py-16">
      <h1 className="text-3xl font-bold tracking-tight text-neutral-800">
        Maestro
      </h1>
      <p className="mt-2 text-base text-neutral-500">
        Base configurada. Tipografia <span className="font-medium">Nu Sans</span>, paleta NuDS,
        layout enxuto (header + drawer + modal).
      </p>

      <div className="mt-8 grid gap-4">
        <Card>
          <h2 className="text-base font-semibold text-neutral-800">Conexão com backend</h2>
          <p className="mt-1 text-sm text-neutral-500">
            Verifica se a API local está respondendo em <code>/health</code>.
          </p>
          <div className="mt-4 flex items-center gap-3">
            <Button onClick={pingBackend} loading={loading} disabled={loading}>
              Testar backend
            </Button>
            <Button variant="secondary" onClick={() => setModalOpen(true)}>
              Sobre
            </Button>
          </div>
          {health && (
            <pre className="mt-4 overflow-x-auto rounded-lg bg-neutral-100 p-4 text-xs text-neutral-700">
{JSON.stringify(health, null, 2)}
            </pre>
          )}
        </Card>
      </div>

      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title="Sobre o Maestro"
        footer={
          <Button variant="secondary" onClick={() => setModalOpen(false)}>
            Fechar
          </Button>
        }
      >
        <p>
          Maestro é um assistente <strong>local-first</strong> para Engineering Management.
          Esta é a base do projeto: backend FastAPI, frontend React + Tailwind, e a estrutura
          de skills/agents do Claude Code já prontas para receber as features.
        </p>
      </Modal>
    </section>
  );
}
