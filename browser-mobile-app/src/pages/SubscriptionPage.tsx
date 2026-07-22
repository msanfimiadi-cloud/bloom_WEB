import { useCallback, useState } from 'react';
import { ContentText } from '../components/ContentText';
import { SubscriptionPaymentCard } from '../components/SubscriptionPaymentCard';
import { useContentText } from '../content/ContentContext';
import type { AcquiringPayment, ClientProfile, PaymentRequest, Subscription, SubscriptionPlan } from '../api/types';
import { formatDate } from '../utils/format';
import { getSubscriptionEnd, isSubscriptionActive } from '../utils/subscription';

interface SubscriptionPageProps {
  profile: ClientProfile | null;
  subscription: Subscription | null;
  paymentRequest: PaymentRequest | null;
  isCreatingPayment: boolean;
  onCreatePayment: (email: string, subscriptionPlanId: number) => Promise<AcquiringPayment | null>;
  onActivateTrial: () => Promise<Subscription>;
  onBack: () => void;
}

export function SubscriptionPage({
  profile,
  subscription,
  isCreatingPayment,
  onCreatePayment,
  onActivateTrial,
  onBack,
}: SubscriptionPageProps) {
  const [plan, setPlan] = useState<SubscriptionPlan | null>(null);
  const accessEnd = getSubscriptionEnd(subscription);
  const hasAccess = isSubscriptionActive(subscription);
  const backLabel = useContentText('subscription.back', '← Назад');
  const priceLabel = plan ? Number(plan.price).toLocaleString('ru-RU', { maximumFractionDigits: 2 }) : '';
  const handlePlanLoaded = useCallback((nextPlan: SubscriptionPlan | null) => setPlan(nextPlan), []);

  return (
    <section className="page">
      <button className="link-button" type="button" onClick={onBack}>{backLabel}</button>
      <SubscriptionPaymentCard profile={profile} subscription={subscription} isCreatingPayment={isCreatingPayment} onCreatePayment={onCreatePayment} onActivateTrial={onActivateTrial} onPlanLoaded={handlePlanLoaded} />

      <div className="info-panel">
        <ContentText as="strong" textKey="subscription.current_access.title" fallback="Текущий доступ" />
        <p>{hasAccess ? `Доступ активен до ${formatDate(accessEnd)}` : 'Доступ не активен'}</p>
      </div>

      <div className="terms-list">
        <ContentText as="h2" textKey="subscription.terms.title" fallback="Условия подписки" />
        <ul>
          <li>Стоимость — {plan ? `${priceLabel} ₽` : 'уточняется'}.</li>
          <li>Доступ открывается на {plan ? `${plan.duration_days} дней` : 'срок тарифа'}.</li>
          <li>Автопродление не подключено.</li>
          <li>Продление выполняется вручную.</li>
          <li>Привилегии зависят от условий конкретного партнёра.</li>
        </ul>
      </div>
    </section>
  );
}
