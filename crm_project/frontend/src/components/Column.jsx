import React from "react";
import { useDroppable } from "@dnd-kit/core";
import Card from "./Card";

export default function Column({ id, title, items = [] }) {
  const { setNodeRef } = useDroppable({ id });

  return (
    <div ref={setNodeRef} className="w-64 bg-gray-200 p-4 rounded-lg min-h-[300px] flex flex-col">
      <h2 className="font-bold text-lg text-center">{title}</h2>
      {items.length > 0 ? (
        items.map((item, index) => <Card key={index} item={item} />)
      ) : (
        <p className="text-gray-500 text-center">Нет данных</p>
      )}
    </div>
  );
}
