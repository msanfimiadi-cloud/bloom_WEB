import type { ReactNode } from 'react';
import type { PageId } from '../App';

function HomeIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <path d="M3.8 10.8 12 4l8.2 6.8" />
      <path d="M6.3 9.7v9.1h11.4V9.7" />
      <path d="M9.8 18.8v-5h4.4v5" />
    </svg>
  );
}

function PartnersIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <path d="M12 3.8v16.4" />
      <path d="M4.4 8.2h15.2" />
      <path d="M6.5 8.2 4.8 13h5.1L8.2 8.2" />
      <path d="M17.5 8.2 15.8 13h5.1l-1.7-4.8" />
      <path d="M8.8 20.2h6.4" />
    </svg>
  );
}

function PrivilegesIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <path d="M12 3.4 15 8l5.2 1.4-3.4 4.2.3 5.4-5.1-2-5.1 2 .3-5.4-3.4-4.2L9 8z" />
      <path d="m9.6 12 1.7 1.7 3.4-3.8" />
    </svg>
  );
}

function SavingsIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <path d="M7 6.7h7.1a4 4 0 0 1 0 8H7" />
      <path d="M7 10.7h8.1" />
      <path d="M7 3.8v16.4" />
    </svg>
  );
}

function ProfileIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <path d="M12 12.2a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z" />
      <path d="M4.8 20.2c.8-3.8 3.4-5.8 7.2-5.8s6.4 2 7.2 5.8" />
    </svg>
  );
}

// static regression labels: Главная Партнёры Мои привилегии Экономия Профиль
const items: Array<{ id: PageId; label: string; icon: ReactNode }> = [
  { id: 'home', label: 'Главная', icon: <HomeIcon /> },
  { id: 'catalog', label: 'Партнёры', icon: <PartnersIcon /> },
  { id: 'privileges', label: 'Мои привилегии', icon: <PrivilegesIcon /> },
  { id: 'savings', label: 'Экономия', icon: <SavingsIcon /> },
  { id: 'profile', label: 'Профиль', icon: <ProfileIcon /> },
];

interface BottomNavProps {
  activePage: PageId;
  onNavigate: (page: PageId) => void;
}

export function BottomNav({ activePage, onNavigate }: BottomNavProps) {
  return (
    <nav className="bottom-nav" aria-label="Основная навигация">
      {items.map((item) => {
        const isActive = item.id === activePage;

        return (
          <button
            className={isActive ? 'bottom-nav__item bottom-nav__item--active' : 'bottom-nav__item'}
            type="button"
            key={item.id}
            onClick={() => onNavigate(item.id)}
            aria-current={isActive ? 'page' : undefined}
          >
            <span className="bottom-nav__content">
              <span className="bottom-nav__icon" aria-hidden="true">{item.icon}</span>
              <span className="bottom-nav__label">{item.label}</span>
            </span>
          </button>
        );
      })}
    </nav>
  );
}
