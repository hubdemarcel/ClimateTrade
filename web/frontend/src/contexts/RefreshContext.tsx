import React, { createContext, useContext, useState, ReactNode } from 'react';

interface RefreshContextType {
  refreshTrigger: Date;
  triggerRefresh: () => void;
  isRefreshing: boolean;
  setIsRefreshing: (refreshing: boolean) => void;
}

const RefreshContext = createContext<RefreshContextType | undefined>(undefined);

export const useRefresh = () => {
  const context = useContext(RefreshContext);
  if (context === undefined) {
    throw new Error('useRefresh must be used within a RefreshProvider');
  }
  return context;
};

interface RefreshProviderProps {
  children: ReactNode;
}

export const RefreshProvider: React.FC<RefreshProviderProps> = ({ children }) => {
  const [refreshTrigger, setRefreshTrigger] = useState<Date>(new Date());
  const [isRefreshing, setIsRefreshing] = useState(false);

  const triggerRefresh = () => {
    setRefreshTrigger(new Date());
  };

  const value = {
    refreshTrigger,
    triggerRefresh,
    isRefreshing,
    setIsRefreshing,
  };

  return (
    <RefreshContext.Provider value={value}>
      {children}
    </RefreshContext.Provider>
  );
};