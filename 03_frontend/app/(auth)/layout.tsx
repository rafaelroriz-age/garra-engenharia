import { Logo } from "@/components/brand/logo";
import { RegistroMarks } from "@/components/prancha/registro-marks";

/**
 * Layout de autenticação "prancha": à esquerda (desktop) uma folha em tinta
 * com malha milimetrada e o selo da prancha; à direita o formulário
 * sobre papel milimetrado. No mobile, só o formulário.
 */
export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="grid min-h-dvh lg:grid-cols-[minmax(0,1.15fr)_minmax(0,1fr)]">
      <aside
        className="prancha-grid-tinta relative hidden flex-col justify-between overflow-hidden p-10 text-sidebar-foreground lg:flex xl:p-14"
      >
        <RegistroMarks inset={20} size={16} className="text-sidebar-muted" />
        <Logo variant="horizontal" />

        <div className="max-w-xl">
          <p className="display-wide text-4xl font-bold uppercase leading-[1.02] tracking-tight xl:text-5xl">
            Sistema de Automação de Relatórios Prediais
          </p>
          <div aria-hidden="true" className="mt-6 h-[3px] w-16 bg-sinal" />
        </div>

        {/* Selo da prancha (title block) */}
        <dl className="w-full max-w-md border border-sidebar-border text-left">
          <div className="px-3 py-2">
            <dt className="rotulo text-[0.625rem] text-sidebar-muted">Entrega</dt>
            <dd className="dado mt-0.5 text-sm">Relatório em PDF e DOCX editável</dd>
          </div>
        </dl>
      </aside>

      <div className="prancha-grid relative flex items-center justify-center px-4 py-10 sm:px-8">
        {children}
      </div>
    </div>
  );
}
