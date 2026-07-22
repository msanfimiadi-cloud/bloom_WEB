import { useEffect, useState } from 'react';
import { getSubscriptionPlans, isApiError, isTimeoutError } from '../api/client';
import { ContentText } from '../components/ContentText';
import { useContentText } from '../content/ContentContext';
import type { AcquiringPayment, ClientProfile, PaymentRequest, Subscription, SubscriptionPlan } from '../api/types';
import { formatDate } from '../utils/format';
import { getSubscriptionEnd, isSubscriptionActive, isTrialEligible } from '../utils/subscription';

interface SubscriptionPageProps {
  profile: ClientProfile | null;
  subscription: Subscription | null;
  paymentRequest: PaymentRequest | null;
  isCreatingPayment: boolean;
  onCreatePayment: (email: string, subscriptionPlanId: number) => Promise<AcquiringPayment | null>;
  onActivateTrial: () => Promise<Subscription>;
  onBack: () => void;
}

function getTrialErrorMessage(error: unknown): string {
  if (isTimeoutError(error)) {
    return 'Загрузка заняла слишком много времени. Попробуйте ещё раз.';
  }

  if (isApiError(error) && error.status === 409) {
    return 'У вас уже есть активный доступ';
  }

  if (isApiError(error) && [400, 403, 422].includes(error.status || 0)) {
    return 'Пробный период уже использован';
  }

  return 'Не удалось активировать тестовый период. Попробуйте ещё раз.';
}

export function SubscriptionPage({
  profile,
  subscription,
  isCreatingPayment,
  onCreatePayment,
  onActivateTrial,
  onBack,
}: SubscriptionPageProps) {
  const [isActivatingTrial, setIsActivatingTrial] = useState(false);
  const [localError, setLocalError] = useState('');
  const [receiptEmail, setReceiptEmail] = useState(String(profile?.contact_email || profile?.email || ''));
  const [acceptedOffer, setAcceptedOffer] = useState(false);
  const [plan, setPlan] = useState<SubscriptionPlan | null>(null);
  const [planLoadError, setPlanLoadError] = useState('');
  const accessEnd = getSubscriptionEnd(subscription);
  const hasAccess = isSubscriptionActive(subscription);
  const trialAvailable = isTrialEligible(profile, subscription);
  const backLabel = useContentText('subscription.back', '← Назад');
  const trialCta = useContentText('subscription.trial.cta', 'Подключить пробный период 15 дней');
  const priceLabel = plan ? Number(plan.price).toLocaleString('ru-RU', { maximumFractionDigits: 2 }) : '';

  useEffect(() => {
    let cancelled = false;
    void getSubscriptionPlans()
      .then((plans) => {
        if (cancelled) return;
        const activePlan = plans.find((item) => item.code === 'monthly') || plans[0] || null;
        setPlan(activePlan);
        setPlanLoadError(activePlan ? '' : 'Активный тариф подписки не найден.');
      })
      .catch(() => {
        if (!cancelled) setPlanLoadError('Не удалось загрузить актуальную стоимость подписки.');
      });
    return () => { cancelled = true; };
  }, []);

  async function handleTrial() {
    setIsActivatingTrial(true);
    setLocalError('');

    try {
      await onActivateTrial();
    } catch (caughtError) {
      setLocalError(getTrialErrorMessage(caughtError));
    } finally {
      setIsActivatingTrial(false);
    }
  }

  async function handlePayment() {
    setLocalError('');
    if (!receiptEmail.includes('@')) {
      setLocalError('Укажите email, на который Точка отправит чек.');
      return;
    }
    if (!acceptedOffer) {
      setLocalError('Подтвердите согласие с условиями оферты.');
      return;
    }
    if (!plan) {
      setLocalError(planLoadError || 'Стоимость подписки ещё загружается.');
      return;
    }
    try {
      const payment = await onCreatePayment(receiptEmail, plan.id);
      if (!payment?.payment_url) throw new Error('Payment URL is missing');
      sessionStorage.setItem('bloom.pendingPaymentId', payment.payment_id);
      window.location.assign(String(payment.payment_url));
    } catch {
      setLocalError('Не удалось создать оплату. Попробуйте ещё раз.');
    }
  }

  return (
    <section className="page">
      <button className="link-button" type="button" onClick={onBack}>{backLabel}</button>
      <div className="subscription-card">
        <ContentText as="p" className="eyebrow" textKey="subscription.eyebrow" fallback="Подписка Bloom Club" />
        <h1>{plan ? `${priceLabel} ₽ / ${plan.duration_days} дней` : 'Загружаем стоимость…'}</h1>
        <ContentText as="p" textKey="subscription.description" fallback="Доступ на 1 месяц к клубным привилегиям у партнёров Bloom Club. Автопродление не подключено, продление выполняется вручную." multiline />
        {trialAvailable ? (
          <button className="button button--primary" type="button" onClick={() => void handleTrial()} disabled={isActivatingTrial}>
            {isActivatingTrial ? 'Активируем…' : trialCta}
          </button>
        ) : null}
        <label className="payment-email-field">
          <span>Email для отправки чека</span>
          <input type="email" value={receiptEmail} onChange={(event) => setReceiptEmail(event.target.value)} autoComplete="email" placeholder="name@example.com" />
        </label>
        <label className="payment-consent"><input type="checkbox" checked={acceptedOffer} onChange={(event) => setAcceptedOffer(event.target.checked)} /> <span>Я принимаю условия <a href="/docs/Пользовательское%20соглашение.docx" target="_blank" rel="noreferrer">оферты</a> и условия возврата.</span></label>
        <button className="button button--primary" type="button" onClick={() => void handlePayment()} disabled={isCreatingPayment || !plan}>
          {isCreatingPayment ? 'Создаём оплату…' : plan ? `Оплатить подписку — ${priceLabel} ₽` : 'Стоимость загружается…'}
        </button>
        <small>На странице Точки можно выбрать СБП или банковскую карту.</small>
        {planLoadError ? <p className="error-text">{planLoadError}</p> : null}
        {localError ? <p className="error-text">{localError}</p> : null}
      </div>

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
