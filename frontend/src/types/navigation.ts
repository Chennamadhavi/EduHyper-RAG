import React from 'react';

export type UserRole = 'teacher' | 'student' | 'public';

export interface NavItem {
  title: string;
  path: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
  description?: string;
}

export interface BreadcrumbItem {
  label: string;
  path?: string;
}
