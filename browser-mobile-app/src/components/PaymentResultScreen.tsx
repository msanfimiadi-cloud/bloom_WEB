import { useCallback, useEffect, useState } from 'react';
import { getAcquiringPayment, refreshAcquiringPayment } from '../api/client';
import type { AcquiringPayment } from '../api/types';

interface Props { onDone: () => Promise<void>; onBack: () => void; }

export function PaymentResultScreen({ onDone, onBack }: Props) {
  const params = new URLSearchParams(window.location.search);
  const paymentId = params.get('payment') || sessionStorage.getItem('bloom.pendingPaymentId') || '';
  const [payment, setPayment] = useState<AcquiringPayment | null>(null);
  const [error, setError] = useState(false);

  const check = useCallback(async (force = false) => {
    if (!paymentId) { setError(true); return; }
    try {
      const next = force ? await refreshAcquiringPayment(paymentId) : await getAcquiringPayment(paymentId);
      setPayment(next); setError(false);
      if (next.status === 'approved' && next.subscription_activated) {
        sessionStorage.removeItem('bloom.pendingPaymentId');
        await onDone();
      }
    } catch { setError(true); }
  }, [onDone, paymentId]);

  useEffect(() => {
    void check(true);
    const timer = window.setInterval(() => void check(false), 3000);
    const pageshow = () => void check(false);
    window.addEventListener('pageshow', pageshow);
    return () => { window.clearInterval(timer); window.removeEventListener('pageshow', pageshow); };
  }, [check]);

  const status = payment?.status;
  const title = status === 'approved' ? 'Подписка активирована' : status === 'expired' ? 'Ссылка на оплату истекла' : status === 'failed' || status === 'cancelled' ? 'Оплата не завершена' : error ? 'Не удалось проверить платёж' : 'Проверяем оплату…';
  const text = status === 'approved' ? 'Теперь вам доступны все привилегии Bloom Club.' : status === 'expired' ? 'Создайте новую ссылку на оплату.' : status === 'failed' || status === 'cancelled' ? 'Деньги не были списаны или банк ещё не подтвердил операцию.' : error ? 'Проверьте интернет и повторите проверку.' : 'Обычно это занимает несколько секунд. Мы автоматически обновим статус.';
  return <section className="page"><div className={`subscription-card payment-result payment-result--${status || 'checking'}`}><p className="eyebrow">Оплата Bloom Club</p><h1>{title}</h1><p>{text}</p>{status !== 'approved' && status !== 'expired' ? <button className="button button--primary" type="button" onClick={() => void check(true)}>Проверить ещё раз</button> : null}<button className="link-button" type="button" onClick={onBack}>{status === 'expired' ? 'Создать новую ссылку' : 'Вернуться в приложение'}</button></div></section>;
}
