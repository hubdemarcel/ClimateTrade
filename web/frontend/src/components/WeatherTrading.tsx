import React, { useState, useEffect } from 'react';
import './WeatherTrading.css';

interface TemperatureRange {
  range: string;
  volume: number;
  tokenId: string;
  outcome: 'YES' | 'NO';
  price?: number;
}

interface WeatherMarket {
  city: string;
  date: string;
  eventId: string;
  totalVolume: number;
  ranges: TemperatureRange[];
}

const WeatherTrading: React.FC = () => {
  const [selectedMarket, setSelectedMarket] = useState<WeatherMarket | null>(null);
  const [orderBook, setOrderBook] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string>('');

  // London September 6, 2025 temperature markets
  const londonMarkets: WeatherMarket = {
    city: 'London',
    date: 'September 6, 2025',
    eventId: '41804',
    totalVolume: 87181.75,
    ranges: [
      {
        range: '67°F or below',
        volume: 9805.68,
        tokenId: '96052970375192193965665703460415461799701691467856443210296591623438564899061',
        outcome: 'YES'
      },
      {
        range: '68-69°F',
        volume: 12105.36,
        tokenId: '58962515611180187340041969421928969119375292337508375208509431266504136177439',
        outcome: 'YES'
      },
      {
        range: '70-71°F',
        volume: 11273.10,
        tokenId: '37172390765315093110471389348323286243977311293283126312429163323582163454195',
        outcome: 'YES'
      },
      {
        range: '72-73°F',
        volume: 6109.51,
        tokenId: '52343700455933500408049601929246312355510842460486464806354092979029264318263',
        outcome: 'YES'
      },
      {
        range: '74-75°F',
        volume: 9329.62,
        tokenId: '35300483685814272813272985167603318709315139377186224614390813355563345949507',
        outcome: 'YES'
      },
      {
        range: '76-77°F',
        volume: 17589.16,
        tokenId: '15089624525714059248061235413743672137603963529876877081288102106493687052131',
        outcome: 'YES'
      },
      {
        range: '78°F or higher',
        volume: 20969.31,
        tokenId: '111918100953532359823757051873404328426065100377930181194803363867011618313594',
        outcome: 'YES'
      }
    ]
  };

  useEffect(() => {
    // Load London markets by default
    setSelectedMarket(londonMarkets);
  }, []);

  const fetchOrderBook = async (tokenId: string) => {
    try {
      setLoading(true);
      const response = await fetch(`/api/clob/orderbook/${tokenId}`);
      if (response.ok) {
        const data = await response.json();
        setOrderBook(data);
      } else {
        setMessage('Failed to load order book');
      }
    } catch (error) {
      setMessage('Error loading order book');
    } finally {
      setLoading(false);
    }
  };

  const placeOrder = async (tokenId: string, side: 'BUY' | 'SELL', price: number, size: number) => {
    try {
      setLoading(true);
      const orderData = {
        token_id: tokenId,
        price: price,
        size: size,
        side: side
      };

      const response = await fetch('/api/clob/orders/limit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(orderData),
      });

      if (response.ok) {
        const result = await response.json();
        setMessage(`Order placed successfully! Order ID: ${result.orderId}`);
      } else {
        const error = await response.json();
        setMessage(`Order failed: ${error.detail}`);
      }
    } catch (error) {
      setMessage('Error placing order');
    } finally {
      setLoading(false);
    }
  };

  const handleRangeClick = (range: TemperatureRange) => {
    fetchOrderBook(range.tokenId);
  };

  const handleTrade = (range: TemperatureRange, side: 'BUY' | 'SELL') => {
    const price = side === 'BUY' ? 0.5 : 0.4; // Example prices
    const size = 10; // Example size
    placeOrder(range.tokenId, side, price, size);
  };

  return (
    <div className="weather-trading">
      <div className="trading-header">
        <h1>🌦️ ClimaTrade - Weather Prediction Markets</h1>
        <p>Trade on real weather outcomes using Polymarket CLOB</p>
      </div>

      {message && (
        <div className={`message ${message.includes('success') ? 'success' : 'error'}`}>
          {message}
          <button onClick={() => setMessage('')} className="close-btn">×</button>
        </div>
      )}

      <div className="markets-container">
        {selectedMarket && (
          <div className="market-card">
            <div className="market-header">
              <h2>{selectedMarket.city} - {selectedMarket.date}</h2>
              <div className="market-stats">
                <span className="total-volume">
                  Total Volume: ${selectedMarket.totalVolume.toLocaleString()}
                </span>
                <span className="event-id">Event ID: {selectedMarket.eventId}</span>
              </div>
            </div>

            <div className="temperature-ranges">
              <h3>Temperature Ranges</h3>
              <div className="ranges-grid">
                {selectedMarket.ranges.map((range, index) => (
                  <div key={index} className="range-card">
                    <div className="range-header">
                      <h4>{range.range}</h4>
                      <span className="volume">${range.volume.toLocaleString()}</span>
                    </div>

                    <div className="range-actions">
                      <button
                        className="view-orders-btn"
                        onClick={() => handleRangeClick(range)}
                        disabled={loading}
                      >
                        {loading ? 'Loading...' : 'View Orders'}
                      </button>

                      <div className="trade-buttons">
                        <button
                          className="buy-btn"
                          onClick={() => handleTrade(range, 'BUY')}
                          disabled={loading}
                        >
                          Buy YES
                        </button>
                        <button
                          className="sell-btn"
                          onClick={() => handleTrade(range, 'SELL')}
                          disabled={loading}
                        >
                          Buy NO
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {orderBook && (
          <div className="order-book">
            <h3>Order Book</h3>
            <div className="order-book-content">
              <div className="bids">
                <h4>Bids (Buy Orders)</h4>
                {orderBook.bids && orderBook.bids.length > 0 ? (
                  <div className="orders-list">
                    {orderBook.bids.slice(0, 5).map((bid: any, index: number) => (
                      <div key={index} className="order-item bid">
                        <span>Price: ${bid.price}</span>
                        <span>Size: {bid.size}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p>No bids available</p>
                )}
              </div>

              <div className="asks">
                <h4>Asks (Sell Orders)</h4>
                {orderBook.asks && orderBook.asks.length > 0 ? (
                  <div className="orders-list">
                    {orderBook.asks.slice(0, 5).map((ask: any, index: number) => (
                      <div key={index} className="order-item ask">
                        <span>Price: ${ask.price}</span>
                        <span>Size: {ask.size}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p>No asks available</p>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="trading-info">
        <h3>How Weather Trading Works</h3>
        <div className="info-grid">
          <div className="info-item">
            <h4>📊 Temperature Ranges</h4>
            <p>Bet on which temperature range will occur on September 6, 2025 in London</p>
          </div>
          <div className="info-item">
            <h4>💰 Real Money</h4>
            <p>Trade with real USDC on Polygon blockchain</p>
          </div>
          <div className="info-item">
            <h4>✅ Verified Outcomes</h4>
            <p>Results verified by Weather Underground data</p>
          </div>
          <div className="info-item">
            <h4>🔄 CLOB Trading</h4>
            <p>Centralized order book for efficient price discovery</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WeatherTrading;