import React from 'react';
import { TriangleAlert, InfoIcon,Cloud, Siren } from 'lucide-react';

function NotificationsWidget({ notifications }) {
  const getIcon = (type) => {
    switch (type) {
      case 'warning': return <TriangleAlert className='lucide-icon' />;
      case 'alert': return <Siren className='lucide-icon' />;
      case 'info': return <InfoIcon className='lucide-icon' />;
      default: return <Cloud className='lucide-icon' />;
    }
  };

  return (
    <div className="dashboard-card notifications-widget">
      <div className="card-header">
        <span className="card-icon"><Cloud className='lucide-icon' /></span>
        <h3 className="card-title">Notifications</h3>
      </div>
      <div className="card-content">
        {notifications.length > 0 ? (
          notifications.map(notification => (
            <div key={notification.id} className={`notification-item ${notification.type}`}>
              <span className="notification-icon">{getIcon(notification.type)}</span>
              <span>{notification.message}</span>
            </div>
          ))
        ) : (
          <p className="no-notifications">No notifications</p>
        )}
      </div>
    </div>
  );
}

export default NotificationsWidget;
