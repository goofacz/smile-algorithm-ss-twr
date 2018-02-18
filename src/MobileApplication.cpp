//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see http://www.gnu.org/licenses/.
//

#include <inet/common/ModuleAccess.h>
#include <utilities.h>
#include <algorithm>

#include "CsvLogger.h"
#include "Frame_m.h"
#include "MobileApplication.h"

namespace smile {
namespace algorithm {
namespace ss_twr {

Define_Module(MobileApplication);

const std::string MobileApplication::pollFrameName{"POLL"};
const std::string MobileApplication::responseFrameName{"RESPONSE"};

MobileApplication::~MobileApplication()
{
  if (rxTimeoutTimerMessage) {
    cancelEvent(rxTimeoutTimerMessage.get());
  }
  if (startRangingMessage) {
    cancelEvent(startRangingMessage.get());
  }
}

void MobileApplication::initialize(int stage)
{
  IdealApplication::initialize(stage);

  if (stage == inet::INITSTAGE_LOCAL) {
    rangingRxTimeout = SimTime{par("rangingRxTimeout").longValue(), SIMTIME_MS};
  }

  if (stage == inet::INITSTAGE_APPLICATION_LAYER) {
    auto* mobilesLog = inet::getModuleFromPar<smile::Logger>(par("mobilesLoggerModule"), this, true);
    const auto entry = csv_logger::compose(getMacAddress(), getCurrentTruePosition());
    mobilesLog->append(entry);

    framesLog = inet::getModuleFromPar<smile::Logger>(par("mobileFramesLoggerModule"), this, true);

    rxTimeoutTimerMessage = std::make_unique<cMessage>("Ranging RX timeout");
    startRangingMessage = std::make_unique<cMessage>("Start ranging");

    anchorAddresses.emplace_back("DE-AD-BE-EF-10-01");
    anchorAddresses.emplace_back("DE-AD-BE-EF-10-02");
    anchorAddresses.emplace_back("DE-AD-BE-EF-10-03");
    anchorAddresses.emplace_back("DE-AD-BE-EF-10-04");

    scheduleAt(clockTime(), startRangingMessage.get());
  }
}

void MobileApplication::handleSelfMessage(cMessage* message)
{
  if (message == rxTimeoutTimerMessage.get()) {
    sequenceNumber = sequenceNumber + 3 - (sequenceNumber % 3);
    startRanging();
  }
  else if (message == startRangingMessage.get()) {
    startRanging();
  }
}

void MobileApplication::handleIncommingMessage(cMessage* newMessage)
{
  std::unique_ptr<cMessage>{newMessage};

  const auto nextRangingBeginTimestamp = clockTime() + SimTime{5, SIMTIME_MS};
  scheduleAt(nextRangingBeginTimestamp, startRangingMessage.get());
  cancelEvent(rxTimeoutTimerMessage.get());
}

void MobileApplication::handleTxCompletionSignal(const smile::IdealTxCompletion& completion)
{
  const auto& frame = completion.getFrame();
  if (pollFrameName == frame->getName()) {
    pollTxBeginTimestamp = completion.getOperationBeginClockTimestamp();

    const auto frame = dynamic_cast<const Frame*>(completion.getFrame());
    if (!frame) {
      throw cRuntimeError{"Received signal for %s message, expected PollFrame", frame->getClassName()};
    }

    const auto entry = smile::csv_logger::compose(getMacAddress(), completion, frame->getSequenceNumber());
    framesLog->append(entry);
  }
  else {
    throw cRuntimeError{"Received TX completion signal for unexpected packet of type %s and name \"%s\"",
                        frame->getClassName(), frame->getName()};
  }
}

void MobileApplication::handleRxCompletionSignal(const smile::IdealRxCompletion& completion)
{
  const auto& frame = completion.getFrame();
  if (responseFrameName == frame->getName()) {
    responseRxBeginTimestamp = completion.getOperationBeginClockTimestamp();

    const auto frame = dynamic_cast<const Frame*>(completion.getFrame());
    if (!frame) {
      throw cRuntimeError{"Received signal for %s message, expected ResponseFrame", frame->getClassName()};
    }

    const auto entry = smile::csv_logger::compose(getMacAddress(), completion, frame->getSequenceNumber());
    framesLog->append(entry);
  }
  else {
    throw cRuntimeError{"Received RX completion signal for unexpected packet of type %s and name \"%s\"",
                        frame->getClassName(), frame->getName()};
  }
}

void MobileApplication::startRanging()
{
  const auto& anchorAddress = anchorAddresses.front();
  auto frame = createFrame<Frame>(anchorAddress, pollFrameName.c_str());
  frame->setBitLength(10);
  frame->setSequenceNumber(sequenceNumber);

  sendDelayed(frame.release(), 0, "out");

  const auto rxTimeout = clockTime() + rangingRxTimeout;
  scheduleAt(rxTimeout, rxTimeoutTimerMessage.get());

  pollTxBeginTimestamp = SimTime::ZERO;
  responseRxBeginTimestamp = SimTime::ZERO;

  sequenceNumber++;
  std::rotate(anchorAddresses.begin(), std::next(anchorAddresses.begin()), anchorAddresses.end());
}

}  // namespace ss_twr
}  // namespace algorithm
}  // namespace smile
