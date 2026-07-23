import { NavLink, Outlet } from 'react-router-dom';

const links = [
  { to: '/', label: 'Dashboard', icon: '📊' },
  { to: '/maintenance', label: 'Maintenance', icon: '🔧' },
  { to: '/network', label: 'Network', icon: '🌐' },
  { to: '/workforce', label: 'Workforce', icon: '👷' },
];

export default function Layout() {
  return (
    <div className="flex min-h-screen">
      <nav className="w-52 bg-slate-900 border-r border-slate-800 p-4 flex flex-col gap-1 shrink-0">
        <div className="text-lg font-bold text-white mb-4 px-2">NexusFab</div>
        {links.map((l) => (
          <NavLink
            key={l.to}
            to={l.to}
            end={l.to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-2 px-3 py-2 rounded text-sm transition-colors ${
                isActive ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white hover:bg-slate-800'
              }`
            }
          >
            <span>{l.icon}</span>
            {l.label}
          </NavLink>
        ))}
      </nav>
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
