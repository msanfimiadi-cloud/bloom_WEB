import type { ClientProfile, Subscription } from '../api/types';
import { formatDate } from '../utils/format';
import { getSubscriptionEnd, isSubscriptionActive, isTrialEligible } from '../utils/subscription';
import { toText } from '../utils/text';

interface SubscriptionStatusWidgetProps {
  profile: ClientProfile | null;
  subscription: Subscription | null;
  onOpenSubscription: () => void;
}

function isTrialSubscription(subscription: Subscription | null | undefined): boolean {
  const status = toText(subscription?.status).toLowerCase();
  const source = (subscription || {}) as Record<string, unknown>;
  return status.includes('trial') || source.is_trial === true || source.trial === true;
}

export function SubscriptionStatusWidget({ profile, subscription, onOpenSubscription }: SubscriptionStatusWidgetProps) {
  const end = getSubscriptionEnd(subscription);
  const endLabel = end ? `до ${formatDate(end)}` : '';
  const isActive = isSubscriptionActive(subscription);
  const isTrial = isActive && isTrialSubscription(subscription);
  const trialAvailable = !isActive && isTrialEligible(profile, subscription);
  const canBuy = !isActive && !trialAvailable;
  const statusLabel = isTrial ? 'Тестовый период' : isActive ? 'Активна' : 'Не активна';

  return (
    <aside className={`subscription-widget${isActive ? ' subscription-widget--active' : ' subscription-widget--inactive'}`} aria-label="Статус подписки">
      <span>Статус подписки</span>
      <strong>{statusLabel}</strong>
      {isActive && endLabel ? <small>{endLabel}</small> : null}
      {trialAvailable ? (
        <button className="subscription-widget__button" type="button" onClick={onOpenSubscription}>
          Оформить доступ
        </button>
      ) : null}
      {canBuy ? (
        <button className="subscription-widget__button" type="button" onClick={onOpenSubscription}>
          Купить подписку
        </button>
      ) : null}
    </aside>
  );
}
