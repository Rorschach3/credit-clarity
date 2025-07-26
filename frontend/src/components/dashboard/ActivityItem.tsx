
import { ReactNode } from "react";

interface ActivityItemProps {
  icon: ReactNode;
  iconBgClass: string;
  title: string;
  time: string;
}

export function ActivityItem({ icon, iconBgClass, title, time }: ActivityItemProps) {
  return (
    <div className="flex items-start space-x-4">
      <div className={`${iconBgClass} p-2 rounded-full`}>
        {icon}
      </div>
      <div>
        <p className="font-medium">{title}</p>
        <p className="text-sm text-gray-500">{time}</p>
      </div>
    </div>
  );
}
