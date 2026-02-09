"use client";

import { Download, CreditCard, FileText, ExternalLink } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface Invoice {
  id: string;
  date: string;
  amount: number;
  status: string;
  pdf_url?: string;
}

interface InvoiceHistoryProps {
  invoices: Invoice[];
  onDownload?: (invoiceId: string) => void;
}

export function InvoiceHistory({ invoices, onDownload }: InvoiceHistoryProps) {
  const formatPrice = (amountCents: number) => {
    return (amountCents / 100).toLocaleString('en-US', {
      style: 'currency',
      currency: 'EUR'
    });
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      paid: { color: "bg-green-500", text: "Paid" },
      pending: { color: "bg-yellow-500", text: "Pending" },
      failed: { color: "bg-red-500", text: "Failed" },
      refunded: { color: "bg-gray-500", text: "Refunded" }
    };

    const config = statusConfig[status as keyof typeof statusConfig] || {
      color: "bg-gray-500",
      text: status.charAt(0).toUpperCase() + status.slice(1)
    };

    return (
      <Badge className={`${config.color} text-white text-xs`}>
        {config.text}
      </Badge>
    );
  };

  const handleDownload = (invoice: Invoice) => {
    if (invoice.pdf_url) {
      // Open PDF in new tab
      window.open(invoice.pdf_url, "_blank");
    } else if (onDownload) {
      // Custom download handler
      onDownload(invoice.id);
    }
  };

  if (!invoices || invoices.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <FileText className="w-5 h-5 mr-2" />
            Invoice History
          </CardTitle>
          <CardDescription>
            Your billing invoices and receipts
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <FileText className="w-6 h-6 text-gray-400" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No invoices yet</h3>
            <p className="text-gray-600 text-sm">
              Your billing history will appear here once you have a paid subscription.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center">
          <FileText className="w-5 h-5 mr-2" />
          Invoice History
        </CardTitle>
        <CardDescription>
          Download your billing invoices and receipts
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {invoices.map((invoice) => (
            <div
              key={invoice.id}
              className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:border-gray-300 transition-colors"
            >
              <div className="flex items-center">
                <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center mr-4">
                  <CreditCard className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <div className="flex items-center gap-3 mb-1">
                    <p className="font-medium text-gray-900">
                      Invoice #{invoice.id.slice(-8).toUpperCase()}
                    </p>
                    {getStatusBadge(invoice.status)}
                  </div>
                  <p className="text-sm text-gray-600">
                    {formatDate(invoice.date)}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-4">
                <div className="text-right">
                  <p className="font-medium text-gray-900">
                    {formatPrice(invoice.amount)}
                  </p>
                  <p className="text-xs text-gray-500">
                    EUR
                  </p>
                </div>

                {/* Download Button */}
                {(invoice.pdf_url || onDownload) && invoice.status === "paid" && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleDownload(invoice)}
                    className="h-8"
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Download
                  </Button>
                )}

                {/* View Details Button for pending/failed */}
                {invoice.status !== "paid" && (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => {
                      // Could open a modal with more details or redirect to Stripe
                      window.open(`https://dashboard.stripe.com/`, "_blank");
                    }}
                    className="h-8"
                  >
                    <ExternalLink className="w-4 h-4 mr-2" />
                    Details
                  </Button>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Footer with helpful information */}
        <div className="border-t mt-6 pt-4">
          <div className="text-sm text-gray-600">
            <p className="mb-2">
              <strong>Need help?</strong> Contact our support team if you have questions about your billing.
            </p>
            <div className="flex items-center justify-between">
              <span>All payments are processed securely through Stripe</span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => window.open("mailto:billing@shortcut.ai", "_blank")}
              >
                Contact Support
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}