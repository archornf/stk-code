#!/usr/bin/env python3
#
#  SuperTuxKart - a fun racing game with go-kart
#  Copyright (C) 2006-2015 SuperTuxKart-Team
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

# This script creates the output for the AbstractCharacteristics
# It takes an argument that specifies what the output of the script should be.
# The output options can be seen by running this script without arguments.

import sys

# Input data
#FIXME is wheelPosition needed??
characteristics = """Suspension: stiffness, rest, travelCm, expSpringResponse, maxForce
Stability: rollInfluence, chassisLinearDamping, chassisAngularDamping, downwardImpulseFactor, trackConnectionAccel, smoothFlyingImpulse
Turn: radius(InterpolationArray), timeResetSteer, timeFullSteer(InterpolationArray)
Engine: power, maxSpeed, brakeFactor, brakeTimeIncrease, maxSpeedReverseRatio
Gear: switchRatio(std::vector<float>/floatVector), powerIncrease(std::vector<float>/floatVector)
Mass
Wheels: dampingRelaxation, dampingCompression, radius, position(std::vector<float>/floatVector)
Camera: distance, forwardUpAngle, backwardUpAngle
Jump: animationTime
Lean: max, speed
Anvil: duration, weight, speedFactor
Parachute: friction, duration, durationOther, lboundFranction, uboundFranction, maxSpeed
Bubblegum: duration, speedFraction, torque, fadeInTime, shieldDuration
Zipper: duration, force, speedGain, speedIncrease, fadeOutTime
Swatter: duration, distance, squashDuration, squashSlowdown
Plunger: maxLength, force, duration, speedIncrease, fadeOutTime, inFaceTime
Startup: time(std::vector<float>/floatVector), boost(std::vector<float>/floatVector)
Rescue: duration, vertOffset, height
Explosion: duration, radius, invulnerabilityTime
Nitro: duration, engineForce, consumption, smallContainer, bigContainer, maxSpeedIncrease, fadeOutTime, max
Slipstream: duration, length, width, collectTime, useTime, addPower, minSpeed, maxSpeedIncrease, fadeOutTime"""


class GroupMember:
    def __init__(self, name, typeC, typeStr):
        self.name = name
        self.typeC = typeC
        self.typeStr = typeStr

    def shouldMove(self):
        return self.typeC != "float"

    """E.g. power(std::vector<float>/floatVector)
       or speed(InterpolationArray)
       The default type is float"""
    def parse(content):
        typeC = "float"
        typeStr = typeC
        name = content.strip()
        pos = content.find("(")
        end = content.find(")", pos)
        if pos != -1 and end != -1:
            name = content[:pos].strip()
            pos2 = content.find("/", pos, end)
            if pos2 != -1:
                typeC = content[pos + 1:pos2].strip()
                typeStr = content[pos2 + 1:end].strip()
            else:
                typeC = content[pos + 1:end].strip()
                typeStr = typeC

        return GroupMember(name, typeC, typeStr)

class Group:
    def __init__(self, baseName):
        self.baseName = baseName
        self.members = []

    def addMember(self, content):
        self.members.append(GroupMember.parse(content))

    def getBaseName(self):
        if len(self.baseName) == 0 and len(self.members) > 0:
            return self.members[0].name
        return self.baseName

    """E.g. engine: power, gears(std::vector<Gear>/Gears)
       or mass(float) or only mass"""
    def parse(content):
        pos = content.find(":")
        if pos == -1:
            group = Group("")
            group.addMember(content)
            return group
        else:
            group = Group(content[:pos].strip())
            for m in content[pos + 1:].split(","):
                group.addMember(m)
            return group

"""Creates a list of words from a titlecase string"""
def toList(name):
    result = []
    cur = ""
    for c in name:
        if c.isupper() and len(cur) != 0:
            result.append(cur)
            cur = ""
        cur += c.lower()
    if len(cur) != 0:
        result.append(cur)
    return result

"""titleCase: true  = result is titlecase
              false = result has underscores"""
def joinSubName(group, member, titleCase):
    words = toList(group.baseName) + toList(member.name)
    first = True
    if titleCase:
        words = [w.title() for w in words]
        return "".join(words)
    else:
        return "_".join(words)

def main():
    # Find out what to do
    if len(sys.argv) == 1:
        print("Please specify what you want to know [enum/defs/getter/getType/getXml]")
        return
    task = sys.argv[1]

    groups = [Group.parse(line) for line in characteristics.split("\n")]

    # Find longest name to align the function bodies
    nameLengthTitle = 0
    nameLengthUnderscore = 0
    for g in groups:
        for m in g.members:
            l = len(joinSubName(g, m, True))
            if l > nameLengthTitle:
                nameLengthTitle = l
            l = len(joinSubName(g, m, False))
            if l > nameLengthUnderscore:
                nameLengthUnderscore = l

    # Print the results
    if task == "enum":
        for g in groups:
            print()
            print("        // {0}".format(g.getBaseName().title()))
            for m in g.members:
                print("        {0},".format(joinSubName(g, m, False).upper()))
    elif task == "defs":
        for g in groups:
            print()
            for m in g.members:
                nameTitle = joinSubName(g, m, True)
                nameUnderscore = joinSubName(g, m, False)
                if m.shouldMove():
                    typeC = m.typeC + "&&"
                else:
                    typeC = m.typeC

                print("    {0} get{1}() const;".
                    format(typeC, nameTitle, nameUnderscore))
    elif task == "getter":
        for g in groups:
            for m in g.members:
                nameTitle = joinSubName(g, m, True)
                nameUnderscore = joinSubName(g, m, False)
                if m.shouldMove():
                    typeC = m.typeC + "&&"
                    result = "std::move(result)"
                else:
                    typeC = m.typeC
                    result = "result"

                print("""{3} AbstractCharacteristics::get{1}() const
{{
    {0} result;
    bool isSet = false;
    process({2}, &result, &isSet);
    if (!isSet)
        Log::fatal("AbstractCharacteristics", "Can't get characteristic {2}");
    return {4};
}}
""".format(m.typeC, nameTitle, nameUnderscore.upper(), typeC, result))
    elif task == "getType":
        for g in groups:
            for m in g.members:
                nameTitle = joinSubName(g, m, True)
                nameUnderscore = joinSubName(g, m, False)
                print("""    case {0}:\n        return TYPE_{1};""".
                    format(nameUnderscore.upper(), "_".join(toList(m.typeStr)).upper()))
    elif task == "getXml":
        for g in groups:
            print("    if (const XMLNode *sub_node = node->getNode(\"{0}\"))\n    {{".
                format(g.baseName))
            for m in g.members:
                nameUnderscore = joinSubName(g, m, False)
                nameMinus = "-".join(toList(m.name))
                print("        sub_node->get(\"{0}\", &m_values[{1}]);".
                    format(nameMinus, nameUnderscore.upper()))
            print("    }\n")
    else:
        print("Unknown task")

    #print("Constructor ****************************************")
    #lineLength = 4;
    #line = "    "
    #for g in groups:
    #    for n in g.subNames:
    #        name = "m_{0} = ".format(joinSubName(g, n, False))
    #        l = len(name)
    #        if lineLength + l > 80 and lineLength > 4:
    #            print(line)
    #            line = "    " + name
    #            lineLength = l + 4
    #        else:
    #            line += name
    #            lineLength += l
    #if lineLength > 4:
    #    line += "1;"
    #    print(line)

if __name__ == '__main__':
    main()

