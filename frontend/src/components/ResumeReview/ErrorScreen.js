export default function ErrorScreen({ message }) {
    return (
      <div className="min-h-screen bg-gray-900 p-8 flex items-center justify-center">
        <div className="text-red-500 text-xl">{message}</div>
      </div>
    );
  }