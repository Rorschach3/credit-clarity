import React, { useState } from 'react';
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import useActivityMonitoring from "@/hooks/use-activity-monitoring";

const PostageManagement = () => {
  const [carrier, setCarrier] = useState('');
  const [recipientName, setRecipientName] = useState('');
  const [recipientAddress1, setRecipientAddress1] = useState('');
  const [recipientAddress2, setRecipientAddress2] = useState('');
  const [recipientCity, setRecipientCity] = useState('');
  const [recipientState, setRecipientState] = useState('');
  const [recipientZip, setRecipientZip] = useState('');
  const [shippingRates, setShippingRates] = useState<{ [key: string]: string } | null>(null);
  const [labelUrl, setLabelUrl] = useState('');
  useActivityMonitoring("Viewed Postage Management");

  const handleCarrierChange = (value: string) => {
    setCarrier(value);
    setShippingRates(null);
    setLabelUrl('');
  };

  const handleAddressChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    switch (name) {
      case 'recipientName':
        setRecipientName(value);
        break;
      case 'recipientAddress1':
        setRecipientAddress1(value);
        break;
      case 'recipientAddress2':
        setRecipientAddress2(value);
        break;
      case 'recipientCity':
        setRecipientCity(value);
        break;
      case 'recipientState':
        setRecipientState(value);
        break;
      case 'recipientZip':
        setRecipientZip(value);
        break;
      default:
        break;
    }
  };

  const fetchShippingRates = async () => {
    // Mock API call
    if (!carrier) {
      alert('Please select a carrier.');
      return;
    }

    // Simulate API call delay
    await new Promise((resolve) => setTimeout(resolve, 1000));

    if (carrier === 'usps') {
      setShippingRates({
        priorityMail: '$7.99',
        firstClass: '$3.99',
      });
    } else if (carrier === 'fedex') {
      setShippingRates({
        ground: '$9.99',
        express: '$14.99',
      });
    } else {
      setShippingRates(null);
    }
  };

  const generateLabel = async () => {
    // Mock API call
    if (!carrier || !shippingRates) {
      alert('Please fetch shipping rates first.');
      return;
    }

    // Simulate API call delay
    await new Promise((resolve) => setTimeout(resolve, 1000));

    // Mock label generation
    setLabelUrl('https://via.placeholder.com/150'); // Replace with actual label URL
    useActivityMonitoring("Generated Shipping Label");
  };

  return (
    <div>
      <h2>Postage Management</h2>

      <div className="mb-4">
        <Label htmlFor="carrier" className="block text-sm font-medium text-gray-700">
          Carrier
        </Label>
        <Select onValueChange={handleCarrierChange}>
          <SelectTrigger id="carrier" className="mt-1 w-full">
            <SelectValue placeholder="Select carrier" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="usps">USPS</SelectItem>
            <SelectItem value="fedex">FedEx</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="mb-4">
        <Label htmlFor="recipientName" className="block text-sm font-medium text-gray-700">
          Recipient Name
        </Label>
        <Input
          type="text"
          id="recipientName"
          name="recipientName"
          value={recipientName}
          onChange={handleAddressChange}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
        />
      </div>

      <div className="mb-4">
        <Label htmlFor="recipientAddress1" className="block text-sm font-medium text-gray-700">
          Address Line 1
        </Label>
        <Input
          type="text"
          id="recipientAddress1"
          name="recipientAddress1"
          value={recipientAddress1}
          onChange={handleAddressChange}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
        />
      </div>

      <div className="mb-4">
        <Label htmlFor="recipientAddress2" className="block text-sm font-medium text-gray-700">
          Address Line 2 (Optional)
        </Label>
        <Input
          type="text"
          id="recipientAddress2"
          name="recipientAddress2"
          value={recipientAddress2}
          onChange={handleAddressChange}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
        />
      </div>

      <div className="mb-4">
        <Label htmlFor="recipientCity" className="block text-sm font-medium text-gray-700">
          City
        </Label>
        <Input
          type="text"
          id="recipientCity"
          name="recipientCity"
          value={recipientCity}
          onChange={handleAddressChange}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
        />
      </div>

      <div className="mb-4">
        <Label htmlFor="recipientState" className="block text-sm font-medium text-gray-700">
          State
        </Label>
        <Input
          type="text"
          id="recipientState"
          name="recipientState"
          value={recipientState}
          onChange={handleAddressChange}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
        />
      </div>

      <div className="mb-4">
        <Label htmlFor="recipientZip" className="block text-sm font-medium text-gray-700">
          Zip Code
        </Label>
        <Input
          type="text"
          id="recipientZip"
          name="recipientZip"
          value={recipientZip}
          onChange={handleAddressChange}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
        />
      </div>

      <Button onClick={fetchShippingRates} className="mb-4">Fetch Rates</Button>

      {shippingRates && (
        <div>
          <h3>Shipping Rates</h3>
          <ul>
            {Object.entries(shippingRates).map(([service, rate]) => (
              <li key={service}>{service}: {rate}</li>
            ))}
          </ul>
          <Button onClick={generateLabel}>Generate Label</Button>
        </div>
      )}

      {/* {labelUrl && (
        <div>
          <h3>Shipping Label</h3>
          <img src={labelUrl} alt="Shipping Label" />
        </div>
      )} */}
    </div>
  );
};

export default PostageManagement;
