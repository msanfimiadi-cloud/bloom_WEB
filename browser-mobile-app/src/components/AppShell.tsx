import type { PropsWithChildren } from 'react';
import type { PageId } from '../App';
import type { ClientProfile, Subscription } from '../api/types';
import { BottomNav } from './BottomNav';
import { SubscriptionStatusWidget } from './SubscriptionStatusWidget';

interface AppShellProps extends PropsWithChildren {
  activePage: PageId;
  onNavigate: (page: PageId) => void;
  onHiddenDiagnosticsGesture?: () => void;
  profile?: ClientProfile | null;
  subscription?: Subscription | null;
  onOpenSubscription?: () => void;
}

export function AppShell({ activePage, onNavigate, children, onHiddenDiagnosticsGesture, profile = null, subscription = null, onOpenSubscription }: AppShellProps) {
  return (
    <div className="app-shell">
      <button className="app-shell__diagnostic-hotspot" type="button" aria-label="Открыть диагностику" onClick={onHiddenDiagnosticsGesture} tabIndex={-1}></button>
      {onOpenSubscription ? (
        <SubscriptionStatusWidget profile={profile} subscription={subscription} onOpenSubscription={onOpenSubscription} />
      ) : null}
      <main className="app-shell__content">
        {children}
      </main>
      <BottomNav activePage={activePage} onNavigate={onNavigate} />
    </div>
  );
}
