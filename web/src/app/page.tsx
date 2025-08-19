'use client'

import Link from "next/link"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { MapPin, Calendar, Trophy, TrendingUp, BarChart3, Users } from "lucide-react"

export default function Home() {
  const features = [
    {
      title: "Interactive Circuit Map",
      description: "Explore F1 circuits around the world with detailed information",
      icon: MapPin,
      href: "/map",
      color: "text-blue-500"
    },
    {
      title: "Season Browser",
      description: "Browse races by season with dates and results",
      icon: Calendar,
      href: "/season",
      color: "text-green-500"
    },
    {
      title: "Results Archive",
      description: "Historical race results with detailed statistics",
      icon: Trophy,
      href: "/results",
      color: "text-yellow-500"
    },
    {
      title: "Race Predictor",
      description: "AI-powered race predictions with adjustable parameters",
      icon: TrendingUp,
      href: "/predict",
      color: "text-red-500"
    },
    {
      title: "Analytics Dashboard",
      description: "Deep dive into lap times, strategies, and performance",
      icon: BarChart3,
      href: "/analytics",
      color: "text-purple-500"
    },
    {
      title: "Driver & Team Stats",
      description: "Comprehensive driver and team performance analysis",
      icon: Users,
      href: "/driver",
      color: "text-orange-500"
    }
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-16">
          <h1 className="text-6xl font-bold text-slate-900 dark:text-white mb-4">
            F1 Prediction
            <span className="text-red-500 ml-2">Dashboard</span>
          </h1>
          <p className="text-xl text-slate-600 dark:text-slate-300 max-w-2xl mx-auto">
            Interactive Formula 1 race predictions, analytics, and historical data visualization
          </p>
          <div className="mt-8 flex gap-4 justify-center">
            <Link href="/predict">
              <Button size="lg" className="bg-red-500 hover:bg-red-600">
                Start Predicting
              </Button>
            </Link>
            <Link href="/map">
              <Button size="lg" variant="outline">
                Explore Circuits
              </Button>
            </Link>
          </div>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature) => (
            <Link key={feature.title} href={feature.href}>
              <Card className="h-full transition-all duration-200 hover:shadow-lg hover:-translate-y-1 cursor-pointer">
                <CardHeader>
                  <div className="flex items-center space-x-2">
                    <feature.icon className={`h-6 w-6 ${feature.color}`} />
                    <CardTitle className="text-lg">{feature.title}</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-base">
                    {feature.description}
                  </CardDescription>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>

        {/* Status Section */}
        <div className="mt-16 text-center">
          <div className="bg-white dark:bg-slate-800 rounded-lg p-8 shadow-lg max-w-2xl mx-auto">
            <h2 className="text-2xl font-bold mb-4 text-slate-900 dark:text-white">
              Dashboard Status
            </h2>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-600 dark:text-slate-300">Frontend:</span>
                <span className="text-green-500 font-semibold">Ready ✓</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600 dark:text-slate-300">Backend API:</span>
                <span className="text-yellow-500 font-semibold">Setting up...</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600 dark:text-slate-300">Database:</span>
                <span className="text-yellow-500 font-semibold">Pending</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600 dark:text-slate-300">ML Models:</span>
                <span className="text-yellow-500 font-semibold">In Progress</span>
              </div>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-4">
              This is the initial setup. Features will be progressively enabled.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}