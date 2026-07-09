import type { ReactNode } from 'react';
import type { PageId } from '../App';

interface NavIconProps {
  children: ReactNode;
}

function NavIcon({ children }: NavIconProps) {
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      {children}
    </svg>
  );
}

function HomeIcon() {
  return (
    <NavIcon>
      <path d="m3 9 9-7 9 7" />
      <path d="M5 11v9a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-9" />
      <path d="M9 22V12h6v10" />
    </NavIcon>
  );
}

function PartnersIcon() {
  return (
    <NavIcon>
      <path d="M4 10h16" />
      <path d="M5 10l1.2-5.1A2.4 2.4 0 0 1 8.5 3h7a2.4 2.4 0 0 1 2.3 1.9L19 10" />
      <path d="M5 10v9a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-9" />
      <path d="M9 21v-5a3 3 0 0 1 6 0v5" />
      <path d="M3 10v1a3 3 0 0 0 6 0v-1" />
      <path d="M9 10v1a3 3 0 0 0 6 0v-1" />
      <path d="M15 10v1a3 3 0 0 0 6 0v-1" />
    </NavIcon>
  );
}

function PrivilegesIcon() {
  return (
    <NavIcon>
      <path d="M2 9a3 3 0 0 1 0 6v2a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-2a3 3 0 0 1 0-6V7a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2Z" />
      <path d="m9 15 6-6" />
      <path d="M9 9h.01" />
      <path d="M15 15h.01" />
    </NavIcon>
  );
}

function SavingsIcon() {
  return (
    <NavIcon>
      <path d="M19 7V5a2 2 0 0 0-2-2H5a3 3 0 0 0 0 6h14a2 2 0 0 1 2 2v4h-3a2 2 0 0 0 0 4h3v1a2 2 0 0 1-2 2H5a3 3 0 0 1-3-3V6" />
      <path d="M18 15h.01" />
    </NavIcon>
  );
}

function ProfileIcon() {
  return (
    <NavIcon>
      <circle cx="12" cy="8" r="4" />
      <path d="M20 21a8 8 0 0 0-16 0" />
    </NavIcon>
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
